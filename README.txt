DESCRIPTION

Automates the conversion of online Youtube videos
(or offline audio files or disorganised text files) into Kindle books.
Uses OpenAI's API for transcription and redrafting of the text (for readability).
Requires OpenAI key.

GETTING STARTED

Installation:
pip install youtube-to-kindle

OpenAI:
You will need to provide you own OpenAI key.
Follow the instructions here: https://platform.openai.com/docs/quickstart

QUICKSTART

1. Convert a single Youtube video
2. Convert a single audiofile
3. Convert a Youtube Playlist
4. Convert multiple Youtube videos
5. Convert multiple audiofiles
6. Convert a text file or text files to Kindle
7. Convert without redrafting
8. Estimate the cost of converting all the mp3s in the Download directory
9. Estimate the cost of redrafting all the text files in the Download directory

All code below must be preceded with:
from youtube_to_kindle import YoutubeToKindle
ytk = YouTubeToKindle(openai_key="your_openai_key_here")
ytk.set_download_dir('Downloads') # set this to any location you want

1. Convert a single YouTubeVideo:
ytk.add_to_files('https://www.youtube.com/watch?v=GWCChO7znyM')
ytk.params['author'] = ''
ytk.params['redraft'] = True
ytk.params['turn_first_video_title_to_book_name'] = True
ytk.params['make_first_video_creator_author'] = True
ytk.make_ebook()

2. Convert multiple YouTubeVideos:
ytk.add_to_files('https://www.youtube.com/watch?v=GWCChO7znyM')
ytk.add_to_files('https://www.youtube.com/watch?v=EUY7Q92aK3w')
ytk.params['title'] = 'Tarantino Videos'
ytk.params['author'] = 'Various'
ytk.params['redraft'] = True
ytk.params['turn_video_title_to_chapter_name'] = True
ytk.make_ebook()

3. Convert a YouTubePlaylist:
ytk.add_to_files('https://www.youtube.com/playlist?list=PLICvGmV1_RRLH25uyKaVYXpBLpbQvlZ8e')
ytk.params['title'] = 'Test Playlist'
ytk.params['author'] = 'Me'
ytk.params['redraft'] = True
ytk.params['turn_playlist_title_to_book_title'] = True
ytk.make_ebook()

4. Convert a single audio file:
ytk.add_to_files('pitchvid.mp3')
ytk.params['title'] = 'Audio File'
ytk.params['author'] = 'Me'
ytk.params['redraft'] = True
ytk.params['turn_filename_root_to_chapter_name'] = True
ytk.make_ebook()

5. Convert a multiple audio files:
ytk.add_to_files('pitchvid.mp3')
ytk.add_to_files('How Tarantino Use Music To Start Writing 😯.mp3')
ytk.params['title'] = 'Audio File'
ytk.params['author'] = 'Me'
ytk.params['redraft'] = True
ytk.params['turn_filename_root_to_chapter_name'] = True
ytk.make_ebook()

6. Convert a multiple text files (.txt) on a Mac:
ytk.add_to_files('Commissioning Execs Session.txt')
ytk.add_to_files('Spec scripts session.txt')
ytk.params['title'] = 'Screenplays'
ytk.params['author'] = 'Writers'
ytk.params['redraft'] = True
ytk.params['turn_filename_root_to_chapter_name'] = True
ytk.params['encoding'] = 'latin-1' # mac encoding
ytk.make_ebook()

7. Convert without redrafting:
ytk.add_to_files('https://www.youtube.com/watch?v=GWCChO7znyM')
ytk.params['author'] = ''
ytk.params['redraft'] = False
ytk.params['turn_first_video_title_to_book_name'] = True
ytk.params['make_first_video_creator_author'] = True
ytk.make_ebook()

8. Estimate the cost of converting all the mp3s in the Download directory:
print(ytk.estimate_cost(file_type=".mp3"))

9. Estimate the cost of redrafting all the text files in the Download directory:
print(ytk.estimate_cost(file_type=".txt"))
