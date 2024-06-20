import os
import sys

from youtube_to_kindle import YouTubeToKindle
from keys import KEY
import shutil
ytk = YouTubeToKindle(openai_key=KEY)


def test_convert_single_youtube_video():
    #1. Convert a single YouTubeVideo:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('https://www.youtube.com/watch?v=GWCChO7znyM')
    ytk.params['author'] = ''
    ytk.params['redraft'] = True
    ytk.params['turn_first_video_title_to_book_name'] = True
    ytk.params['make_first_video_creator_author'] = True
    ytk.make_ebook()


def test_convert_multiple_youtube_videos():
    #2. Convert multiple YouTubeVideos:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('https://www.youtube.com/watch?v=GWCChO7znyM')
    ytk.add_to_files('https://www.youtube.com/watch?v=EUY7Q92aK3w')
    ytk.params['title'] = 'Tarantino Videos'
    ytk.params['author'] = 'Various'
    ytk.params['redraft'] = True
    ytk.params['turn_video_title_to_chapter_name'] = True
    ytk.make_ebook()

def test_convert_youtube_playlist():
    #3. Convert a YouTubePlaylist:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('https://www.youtube.com/playlist?list=PLICvGmV1_RRLH25uyKaVYXpBLpbQvlZ8e')
    ytk.params['title'] = 'Test Playlist'
    ytk.params['author'] = 'Me'
    ytk.params['redraft'] = True
    ytk.params['turn_playlist_title_to_book_title'] = True
    ytk.make_ebook()

def test_convert_single_audiofile():
    # 4. Convert a single audiofile:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/pitchvid.mp3')
    ytk.params['title'] = 'Audio File'
    ytk.params['author'] = 'Me'
    ytk.params['redraft'] = True
    ytk.params['turn_filename_root_to_chapter_name'] = True
    ytk.make_ebook()

def test_convert_multiple_audiofiles():
    # 5. Convert a multiple audiofiles:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/pitchvid.mp3')
    ytk.add_to_files('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/How Tarantino Use Music To Start Writing 😯.mp3')
    ytk.params['title'] = 'Audio File'
    ytk.params['author'] = 'Me'
    ytk.params['redraft'] = True
    ytk.params['turn_filename_root_to_chapter_name'] = True
    ytk.make_ebook()

def test_convert_multiple_text_files():
    # 6. Convert multiple text files (.txt) on a Mac:
    ytk.set_download_dir('Downloads')
    ytk.add_to_files('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/test_text.txt')
    ytk.add_to_files('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/test_text2.txt')
    ytk.params['title'] = 'Convert multiple text files (.txt) on a Mac'
    ytk.params['author'] = 'testing.py'
    ytk.params['redraft'] = True
    ytk.params['turn_filename_root_to_chapter_name'] = True
    ytk.params['encoding'] = 'latin-1' # mac encoding
    ytk.make_ebook()
    
def test_get_rewrite_cost():
    print("All costs in $ (i.e. x100)")
    print("Cost to rewrite an empty string:")
    print(100 * ytk.estimate_cost(""))
    print("Cost to rewrite a one character string:")
    print(100 * ytk.estimate_cost("a"))
    test_str = "a b c d e f g"
    print("Cost for rewriting the string ", test_str, " is:")
    print(100*ytk.estimate_cost(test_str))
    print("Cost for transcribing and rewriting the .mp3 file 'pitchvid.mp3' is:")
    # if Downloads_test/mp3s doesn't exist, create it
    if not os.path.exists('Downloads_test'):
        os.mkdir('Downloads_test')
    if not os.path.exists('Downloads_test/mp3'):
        os.mkdir('Downloads_test/mp3')
    # make sure mp3s empty
    for file in os.listdir('Downloads_test/mp3'):
        os.remove('Downloads_test/mp3/' + file)
    # copy pitchvid.mp3 to Downloads_test/mp3s
    shutil.copy('/Users/alexiskirke/Dropbox/Contracting/youtube-to-kindle/testing/pitchvid.mp3', 'Downloads_test/mp3')
    # set download dir to Downloads_test
    ytk.set_download_dir('Downloads_test')
    print("The Below fails for some MP3s because of a bug in tinytag, which is used to estimate the duration of the MP3.")
    print(100*ytk.estimate_cost('.mp3'))
    # delete downloads_test and all subdirs
    shutil.rmtree('Downloads_test')


test_get_rewrite_cost()
#sys.exit()
# get a list of all functions in this python file
test_functions = [test_convert_single_youtube_video, test_convert_single_audiofile, test_convert_multiple_audiofiles, test_convert_multiple_text_files]
# note test_convert_youtube_playlist() depends on all vids being accessible so is left out here
# if the download directory exists, delete it
if os.path.exists('Downloads'):
    shutil.rmtree('Downloads')
# run each function in the list
for test_function in test_functions:
    print("*"*50)
    print("Running test function: ", test_function.__name__)
    test_function()
    # get a list of all txt files in transcriptions and redrafts
    files = os.listdir(os.path.join(ytk.download_dir,'transcriptions'))
    files_redrafts = os.listdir(os.path.join(ytk.download_dir,'redrafts'))
    # sort the list of files
    files.sort()
    files_redrafts.sort()
    # load them in one by one and if redraft is true, check that the redraft is different from the original
    for i in range(len(files)):
        with open(os.path.join(ytk.download_dir,'transcriptions',files[i]), 'r') as f:
            text = f.read()
        with open(os.path.join(ytk.download_dir,'redrafts',files_redrafts[i]), 'r') as f_redraft:
            text_redraft = f_redraft.read()
        if ytk.params['redraft']:
            assert text != text_redraft
        else:
            assert text == text_redraft
    # assert there is an ebook in the Download directory
    assert len([f for f in os.listdir('Downloads') if f.endswith('.epub')]) > 0
    # delete the Download directory and its contents
    shutil.rmtree('Downloads')