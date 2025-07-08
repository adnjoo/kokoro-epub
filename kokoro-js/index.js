import { fileURLToPath } from 'url';
import path, { dirname } from 'path';
import fs from 'fs';
import { EPub } from 'epub2';
import { KokoroTTS } from 'kokoro-js';
import striptags from 'striptags';
import ffmpegPath from 'ffmpeg-static';
import ffmpeg from 'fluent-ffmpeg';
ffmpeg.setFfmpegPath(ffmpegPath);

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function main() {
  const inputDir = path.join(__dirname, 'input');
  const epubFiles = fs.readdirSync(inputDir).filter(f => f.endsWith('.epub'));
  if (epubFiles.length === 0) {
    console.error('No EPUB files found in input/');
    process.exit(1);
  }
  const epubPath = path.join(inputDir, epubFiles[0]);
  console.log('Processing:', epubPath);

  // Parse EPUB
  const epub = new EPub(epubPath);
  await new Promise((resolve, reject) => {
    epub.on('end', resolve);
    epub.on('error', reject);
    epub.parse();
  });

  let fullText = '';
  for (const chapter of epub.flow) {
    const html = await epub.getChapterAsync(chapter.id);
    const text = striptags(html);
    fullText += text + '\n';
  }
  console.log('Text sent to TTS:', fullText.slice(0, 1000));

  // TTS with kokoro-js
  const model_id = 'onnx-community/Kokoro-82M-v1.0-ONNX';
  const tts = await KokoroTTS.from_pretrained(model_id, {
    dtype: 'q8',
    device: 'cpu',
  });

  // Split text into chunks
  function splitText(text, maxLen = 1800) {
    const chunks = [];
    let i = 0;
    while (i < text.length) {
      chunks.push(text.slice(i, i + maxLen));
      i += maxLen;
    }
    return chunks;
  }

  const textChunks = splitText(fullText);
  const chunkFiles = [];

  for (let i = 0; i < textChunks.length; i++) {
    const chunk = textChunks[i];
    console.log(`Generating audio for chunk ${i + 1}/${textChunks.length}`);
    const audio = await tts.generate(chunk, { voice: 'af_heart', format: 'mp3' });
    const chunkPath = path.join(inputDir, `chunk_${i}.mp3`);
    await audio.save(chunkPath);
    chunkFiles.push(chunkPath);
  }

  // Concatenate all chunk MP3s into one output.mp3
  const outputPath = path.join(inputDir, 'output.mp3');
  await new Promise((resolve, reject) => {
    const command = ffmpeg();
    chunkFiles.forEach(f => command.input(f));
    command
      .on('end', resolve)
      .on('error', reject)
      .mergeToFile(outputPath);
  });
  console.log('Audiobook saved to', outputPath);

  // Optionally, clean up chunk files
  chunkFiles.forEach(f => fs.unlinkSync(f));
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
