from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='a')
text = "It was an automatic response to my good grade, a new shade of lipstick, the last popsicle, my expensive haircut. “No fair.” I’d make my fingers like a cross and hold them out between us, as though to protect me from her envy and wrath. I once asked her whether her jealousy had anything to do with her being Jewish, if she thought things came easier to me because I was a WASP."

for i, (_, _, audio) in enumerate(pipeline(text, voice='af_heart')):
    sf.write(f"output_{i}.wav", audio, 24000)
