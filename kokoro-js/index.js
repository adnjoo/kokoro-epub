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
  function splitTextBySentences(text, maxLen = 800) {
    const sentences = text.match(/[^.!?]+[.!?]+[\s]*/g) || [text];
    const chunks = [];
    let chunk = '';

    for (const sentence of sentences) {
      if (sentence.length > maxLen) {
        // If there's content in chunk, push it and start fresh for this long sentence
        if (chunk) {
          chunks.push(chunk.trim() + ' ');
          chunk = '';
        }
        // Now split the long sentence by words, always starting from an empty chunk
        const words = sentence.split(/\s+/);
        for (const word of words) {
          if ((chunk + word + ' ').length > maxLen) {
            if (chunk) chunks.push(chunk.trim() + ' ');
            chunk = word + ' ';
          } else {
            chunk += word + ' ';
          }
        }
      } else {
        if ((chunk + sentence).length > maxLen) {
          if (chunk) chunks.push(chunk.trim() + ' ');
          chunk = sentence;
        } else {
          chunk += sentence;
        }
      }
    }
    console.log(chunk);
    if (chunk) chunks.push(chunk.trim() + ' ');
    return chunks;
  }

  // Seems like around 400 is the max length for TTS
  const textChunks = splitTextBySentences(fullText, 400);
  const chunkFiles = [];

  for (let i = 0; i < textChunks.length; i++) {
    const chunk = textChunks[i];
    console.log(`Chunk ${i + 1} length: ${chunk.length}`);
    console.log(`Generating audio for chunk ${i + 1}/${textChunks.length}:`, chunk.slice(0, 80).replace(/\n/g, ' '), '...');
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
