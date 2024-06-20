import hashlib  # for generating unique identifiers using hash functions
import math  # for mathematical operations like ceiling function
import shutil  # for file operations such as copying and moving files
import ssl  # for handling SSL certificates
import os  # for operating system dependent functionality like file path operations
import openai  # for interacting with OpenAI's API
import tinytag  # for retrieving metadata from audio files
from pydub import AudioSegment  # for audio processing
from pytube import YouTube, Playlist  # for downloading YouTube videos and playlists
from ebooklib import epub  # for creating EPUB files
from typing import List, Dict, Tuple  # for type hinting
import tiktoken  # for tokenizing text for OpenAI models

# Disables SSL certificate verification (use with caution)
ssl._create_default_https_context = ssl._create_unverified_context

# Constant for maximum transcription size in MB
MAX_SIZE = 25

class YouTubeToKindle:
    def __init__(self, download_files: List[str] = None,
                 download_dir: str = "", openai_key: str = "",
                 model: str = 'gpt-4o', max_size: int = MAX_SIZE,
                 chunk_size: int = 512):
        """
        Initialize the YouTubeToKindle class.

        :param download_files: List of audio file paths or URLs.
        :param download_dir: Directory to download and store audio files.
        :param openai_key: API key for OpenAI.
        :param model: Model name for OpenAI.
        :param max_size: Maximum size for transcription files in MB.
        :param chunk_size: Size of chunks used for redrafting in number of words.
        """
        self.total_cost: float = 0  # Total cost of transcription and redrafting
        self.split_files: List[str] = []  # List of split audio files
        self.download_files: List[str] = download_files if download_files else []  # Files to download or process
        self.download_dir: str = download_dir  # Directory to store downloaded files
        self.client = openai.Client(api_key=openai_key)  # OpenAI client for API interactions
        self.model: str = model  # Model name for OpenAI
        self.max_size: int = max_size  # Maximum size for transcription files in MB
        self.files_to_convert: List[str] = []  # List of files to convert to text
        self.files_root: str = ""  # Root directory for files
        self.playlist: str = ""  # Playlist URL if applicable
        self.chunk_size: int = chunk_size  # Size of text chunks for redrafting
        self.cost_per_second: float = 0.0001  # Cost of transcription per second of audio
        self.rewritten_files_list: List[str] = []  # List of filenames of redrafted transcriptions
        self.titles: List[str] = []  # List of titles of videos or audio files
        self.authors: List[str] = []  # List of authors of the content
        self.playlist_title: str = ""  # Title of the playlist if applicable
        self.params: Dict[str, any] = {
            'title': 'YTK Book',  # Default book title
            'author': 'youtube-to-kindle',  # Default author name
            'redraft': True,  # Flag to indicate if redrafting is needed
            'turn_video_title_to_chapter_name': False,  # Flag to use video titles as chapter names
            'turn_first_video_title_to_book_name': False,  # Flag to use first video title as book title
            'turn_filename_root_to_chapter_name': False,  # Flag to use filename roots as chapter names
            'turn_playlist_title_to_book_title': False,  # Flag to use playlist title as book title
            'make_first_video_creator_author': False,  # Flag to use first video creator as author
            'language': 'en',  # Language of the book
            'encoding': 'utf-8',  # Encoding for text files
        }
        # Set unique book identifier using hash of book title
        self.params['identifier'] = hashlib.md5(self.params['title'].encode()).hexdigest()
        # Cost per token for input and output for the specified model
        self.cost_per_token: Dict[str, Dict[str, float]] = {'gpt-4o': {'input': 5 / 1000000, 'output': 15 / 1000000}}
        self.cost_so_far: float = 0  # Running total of the cost so far
        self.average_words_per_second: float = 150 / 60  # Average words per second of speech
        self.average_tokens_per_second: float = self.average_words_per_second * 1.33  # Average tokens per second
        # Prompt to guide the OpenAI model for rewriting text
        self.prompt: str = """
        You are a professional writer and editor who is an expert in non-fiction writing.
        Below is some text which was transcribed directly from audio.
        Please re-write so it does not read like a transcription but like a non-fiction book.
        Also add paragraphing as appropriate.
        Note: some of the text may be direct dialogue quotes from movies. You can leave these as they are.
        Note: if the text is a transcription of a conversation but not movie/TV dialogue, 
        then remove the names of the speakers and re-write as if it is book prose.
        IMPORTANT: This is not the complete transcription, so do not re-write in a
        standalone manner. Also do not leave out ANY information.
        ONLY return the re-written text, with no preamble from yourself.
        Here is the text:
        """
        # Set the appropriate encoding for the chosen model
        if self.model == "gpt-4o":
            self.encoding = tiktoken.encoding_for_model("gpt-4-turbo")
        elif self.model == "gpt-3.5-turbo":
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        # Create subdirectories within the download directory
        self.mp3_dir = os.path.join(self.download_dir, "mp3")
        self.transcriptions_dir = os.path.join(self.download_dir, "transcriptions")
        self.redrafts_dir = os.path.join(self.download_dir, "redrafts")

        os.makedirs(self.mp3_dir, exist_ok=True)
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        os.makedirs(self.redrafts_dir, exist_ok=True)

    def num_tokens(self, text: str) -> int:
        """
        Get the number of tokens in the provided text.

        :param text: The text to tokenize.
        :return: Number of tokens.
        """
        return len(self.encoding.encode(text))  # Encode text and return the number of tokens

    def get_rewrite_cost(self, text: str, input: bool = True) -> float:
        """
        Calculate the cost of rewriting the text based on the number of tokens.

        :param text: The text to rewrite.
        :param input: Whether the text is input or output.
        :return: Cost of rewriting the text.
        """
        direction = "input" if input else "output"  # Determine if cost is for input or output tokens
        tokens = self.num_tokens(text)  # Get number of tokens in the text
        return tokens * self.cost_per_token[self.model][direction]  # Calculate cost based on token count

    def set_download_dir(self, download_dir: str) -> None:
        """
        Set the download directory for audio files.

        :param download_dir: The directory to download and store audio files.
        """
        self.download_dir = download_dir  # Set the download directory
        # Create directory if it does not exist
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Update subdirectories
        self.mp3_dir = os.path.join(self.download_dir, "mp3")
        self.transcriptions_dir = os.path.join(self.download_dir, "transcriptions")
        self.redrafts_dir = os.path.join(self.download_dir, "redrafts")

        os.makedirs(self.mp3_dir, exist_ok=True)
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        os.makedirs(self.redrafts_dir, exist_ok=True)

    def add_to_files(self, file: str) -> None:
        """
        Add a file to the list of files to convert (could be audio, text or YouTube link).

        :param file: The file to add (could be audio or text filename, or YouTube link).
        """
        # If a playlist is provided, add all videos in the playlist to the download files list
        if file.startswith("http") and "/playlist?" in file:
            self.download_files += [v.watch_url for v in Playlist(file).videos]
            self.playlist_title = Playlist(file).title
        else:
            self.download_files.append(file)  # Add individual file to download list

    def send_prompt(self, prompt: str) -> str:
        """
        Send a prompt to the OpenAI model and return the response.

        :param prompt: The prompt to send.
        :return: The response from the model.
        """
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        # Send the prompt to OpenAI and get the response
        completions = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
        )
        return completions.choices[0].message.content  # Return the content of the response

    def download(self) -> None:
        """
        Download YouTube audio or copy audio to the specified directory.
        """
        print("Downloading and/or collecting audio or text...")
        for audio in self.download_files:
            print(audio)
            # If the file is a YouTube link, download the audio
            if audio.startswith("http"):
                yt = YouTube(audio)
                video = yt.streams.filter(only_audio=True).first()  # Get the first audio stream
                out_file = video.download(output_path=self.mp3_dir)  # Download the audio file to mp3 directory
                video_title = yt.title  # Get the video title
                # Remove any non-alphanumeric characters from the title
                video_title = ''.join(e for e in video_title if e.isalnum() or e.isspace())
                self.titles.append(video_title)  # Add the cleaned title to the titles list
                base, ext = os.path.splitext(out_file)  # Split the file path into base and extension
                new_file = base + ".mp3"  # Change extension to .mp3
                os.rename(out_file, new_file)  # Rename the file
                self.authors.append(yt.author)  # Add the video author to the authors list
            else:  # If the file is an audio or text file
                new_file = os.path.basename(audio)  # Get the base name of the file
                # Make the title the filename root without extension
                title = os.path.splitext(os.path.basename(audio))[0]
                self.titles.append(title)  # Add the title to the titles list
                if audio.endswith(".txt") and not os.path.exists(os.path.join(self.transcriptions_dir, new_file)):  # If the file is a text file
                    shutil.copy(audio, os.path.join(self.transcriptions_dir, new_file))  # Copy the file to the transcriptions directory
                elif not os.path.exists(os.path.join(self.mp3_dir, new_file)):   # assume mp3
                    shutil.copy(audio, os.path.join(self.mp3_dir, new_file))  # Copy the file to the mp3 directory
            self.files_to_convert.append(new_file)  # Add the file to the list of files to convert

    def split_mp3(self, file_path: str, chunk_size_mb: int = 0) -> None:
        """
        Split an MP3 file into chunks of approximately the specified size.

        :param file_path: Path to the MP3 file.
        :param chunk_size_mb: Size of each chunk in MB. Defaults to a fraction of max_size.
        """
        if not chunk_size_mb:
            chunk_size_mb = int(0.99 * self.max_size)  # Default chunk size to just under max_size
        chunk_size_bytes = chunk_size_mb * 1024 * 1024  # Convert chunk size to bytes

        audio = AudioSegment.from_mp3(file_path)  # Load the MP3 file
        total_size_bytes = len(audio.raw_data)  # Get the total size of the audio data in bytes
        num_chunks = math.ceil(total_size_bytes / chunk_size_bytes)  # Calculate the number of chunks needed
        chunk_duration_ms = len(audio) / num_chunks  # Calculate the duration of each chunk in milliseconds

        split_files = []  # Initialize the list of split files
        for i in range(num_chunks):
            start_time = i * chunk_duration_ms  # Calculate the start time of the chunk
            end_time = (i + 1) * chunk_duration_ms if (i + 1) * chunk_duration_ms <= len(audio) else len(audio)  # Calculate the end time of the chunk
            chunk = audio[start_time:end_time]  # Extract the chunk from the audio
            filename = ''.join(os.path.basename(file_path).split(".")[:-1]) + f"_chunk_{i + 1}.mp3"  # Create the filename for the chunk
            filename = os.path.join(self.mp3_dir, filename)  # Save split files in mp3 directory
            chunk.export(filename, format="mp3")  # Export the chunk to a file
            split_files.append(filename)  # Add the chunk filename to the list of split files
            print(f"Chunk {i + 1} saved: {filename}")
        # If there is any remaining audio, save it as an additional chunk
        if end_time < len(audio):
            chunk = audio[end_time:]
            filename = ''.join(os.path.basename(file_path).split(".")[:-1]) + f"_chunk_{num_chunks + 1}.mp3"
            filename = os.path.join(self.mp3_dir, filename)
            chunk.export(filename, format="mp3")
            split_files.append(filename)
            print(f"Chunk {num_chunks + 1} saved: {filename}")
        self.split_files = split_files  # Update the split files list

    def chunk_text(self, text: str) -> List[str]:
        """
        Break down text into chunks of at least N words, ending in a full stop.

        :param text: The text to chunk.
        :return: List of text chunks.
        """
        sentences = text.split(".")  # Split text into sentences
        chunks = []  # Initialize list of chunks
        chunk = ""  # Initialize current chunk
        for sentence in sentences:
            if len(chunk.split()) < self.chunk_size:
                chunk += sentence + "."  # Add sentence to chunk
            else:
                chunks.append(chunk)  # Add chunk to list if it reaches the required size
                chunk = ""
        # Add the final chunk if it exists
        if chunk:
            chunks.append(chunk)
        return chunks  # Return the list of chunks

    def save_chunks(self, full_transcription: str, file_path: str) -> Tuple[str, List[str]]:
        """
        Save full transcription to a file as newline separated chunks.

        :param full_transcription: Full transcription text.
        :param file_path: Path to save the chunked text file.
        :return: Path to the saved chunked text file and the list of chunks.
        """
        chunks = self.chunk_text(full_transcription)  # Chunk the transcription text
        chunk_file = os.path.join(self.transcriptions_dir, os.path.splitext(os.path.basename(file_path))[0] + "_chunked.txt")  # Save in transcriptions directory
        with open(chunk_file, "w") as f:
            for c in chunks:
                f.write(c + "\n")  # Write each chunk to the file
        return chunk_file, chunks  # Return the path to the chunked file and the list of chunks

    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe an audio file or re-write text file.

        :param file_path: Path to the audio or text file.
        :return: Path to the rewritten chunks filename.
        """
        filename = os.path.join(self.transcriptions_dir, ''.join(os.path.splitext(os.path.basename(file_path))[:-1]) + ".txt")  # Save transcriptions in transcriptions directory
        if file_path.endswith(".txt"):  # If a text file, read it directly
            with open(file_path, 'r', encoding=self.params['encoding']) as f:
                full_transcription = f.read()
        else:  # If an audio file, transcribe it
            file_size = os.path.getsize(file_path)
            if file_size > self.max_size * 1024 * 1024:  # If file size exceeds max size, split it
                self.split_mp3(file_path)
                files = self.split_files
            else:
                files = [file_path]
            full_transcription = ""
            for file in files:
                print("Transcribing", file)
                with open(file, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",
                    )
                print(transcription.text)
                full_transcription += transcription.text + " "  # Append transcription to full text
                with open(filename, "w") as f:
                    f.write(full_transcription)  # Save transcription to file
        if self.params['redraft']:
            chunk_file, rewritten_chunks_list = self.save_chunks(full_transcription, file_path)
            rewritten_chunks_filename = self.rewrite_chunks(rewritten_chunks_list, filename)
        else:
            rewritten_chunks_filename = filename  # Use original text if not redrafting
        return rewritten_chunks_filename

    def get_audio_duration(self, file_path: str) -> float:
        """
        Get the duration of an audio file.

        :param file_path: Path to the audio file.
        :return: Duration of the audio file in seconds.
        """
        audio = tinytag.TinyTag.get(file_path)  # Retrieve metadata from the audio file
        return audio.duration  # Return the duration of the audio

    def get_transcription_cost(self, duration_seconds: float) -> float:
        """
        Estimate the cost of using the API.

        :param duration_seconds: Duration of the audio file in seconds.
        :return: Cost of transcribing the audio file.
        """
        self.total_cost += duration_seconds * self.cost_per_second  # Add transcription cost to total cost
        return duration_seconds * self.cost_per_second  # Return the transcription cost

    def rewrite_chunks(self, chunks: List[str], file_path: str) -> str:
        """
        Rewrite chunks of text using the OpenAI model.

        :param chunks: List of text chunks.
        :param file_path: Path to save the rewritten text.
        :return: Path to the rewritten text file.
        """
        prompt = self.prompt + "\n" + "{{"  # Prepare the prompt for the OpenAI model
        output_file = os.path.join(self.redrafts_dir, os.path.splitext(os.path.basename(file_path))[0] + "_redrafted.txt")  # Save redrafted files in redrafts directory
        rewritten_text = ""
        print("Rewriting chunks")
        for c in chunks:
            full_prompt = prompt + c + "}}"  # Add chunk to the prompt
            #self.estimate_rewrite_cost(full_prompt)  # Estimate cost for the prompt
            rewrite = self.send_prompt(full_prompt)  # Send prompt to OpenAI model and get the rewrite
            #self.estimate_rewrite_cost(rewrite, input=False)  # Estimate cost for the output
            print(rewrite + "\n" + '-' * 50)
            rewritten_text += rewrite + "\n"  # Append rewrite to the full text
            with open(output_file, "w") as f:
                f.write(rewritten_text + "\n")  # Save the rewritten text to the file
        return output_file

    def transcribe(self) -> None:
        """
        Transcribe all audio files in the download directory.
        """
        print("Transcribing audio files")
        cost = 0
        file_range = self.files_to_convert  # List of files to convert
        for file in file_range:
            if file.endswith(".mp3"):  # Check if the file is an MP3 audio file
                file = os.path.join(self.mp3_dir, file) if self.mp3_dir else file  # Get the full path of the file
                print(file)
                rewritten_chunks_filename = self.transcribe_audio(file)  # Transcribe the audio file
                duration = self.get_audio_duration(file)  # Get the duration of the audio file
                self.rewritten_files_list.append(rewritten_chunks_filename)  # Add the rewritten file to the list
            else:  # If the file is a text file
                file = os.path.join(self.transcriptions_dir, file) if self.transcriptions_dir else file  # Get the full path of the file
                print(file)
                rewritten_chunks_filename = self.transcribe_audio(file)  # Transcribe the text file
                self.rewritten_files_list.append(rewritten_chunks_filename)  # Add the rewritten file to the list

    def text_to_epub(self, text_files: List[str], output_file: str) -> str:
        """
        Convert multiple text files to an EPUB format book with multiple chapters.

        :param text_files: List of paths to the text files.
        :param output_file: Path to save the EPUB file.
        :return: Path to the generated EPUB file.
        """
        book = epub.EpubBook()
        book.set_identifier(self.params['identifier'])  # Set a unique book identifier
        if self.params['turn_first_video_title_to_book_name']:
            book.set_title(self.titles[0])
        elif self.params['turn_playlist_title_to_book_title']:
            book.set_title(self.playlist_title)
        else:
            book.set_title(self.params['title'])
        book.set_language(self.params['language'])
        if self.params['make_first_video_creator_author']:
            book.add_author(self.authors[0])
        else:
            book.add_author(self.params['author'])

        spine = ['nav']  # Initialize the spine of the EPUB book
        toc = []  # Initialize the table of contents

        for c, text_file in enumerate(text_files):
            with open(text_file, encoding=self.params['encoding']) as f:
                text_content = f.read()

            paragraphs = text_content.split('\n')  # Split the text into paragraphs
            html_content = ''.join(f'<p>{paragraph}</p>' for paragraph in paragraphs if paragraph.strip())  # Convert paragraphs to HTML
            if self.params['turn_video_title_to_chapter_name']:
                chapter = epub.EpubHtml(title=f'{self.titles[c]}', file_name=f'chap_{c + 1}.xhtml', lang='en')
                chapter.content = f'<h1>Chapter {c + 1} - {self.titles[c]}</h1>{html_content}'
            elif self.params['turn_filename_root_to_chapter_name']:
                base = os.path.basename(text_file)
                if base.endswith('_redrafted.txt'):
                    base = base[:-len('_redrafted.txt')] + '.txt'  # Remove '_redrafted' from the filename
                base = os.path.splitext(base)[0]  # Remove the extension
                chapter = epub.EpubHtml(title=f'Chapter {c + 1} - {base}', file_name=f'chap_{c + 1}.xhtml', lang='en')
                chapter.content = f'<h1>Chapter {c + 1} - {base}</h1>{html_content}'
            else:
                chapter = epub.EpubHtml(title=f'Chapter {c + 1}', file_name=f'chap_{c + 1}.xhtml', lang='en')
                chapter.content = f'<h1>Chapter {c + 1}</h1>{html_content}'
            book.add_item(chapter)  # Add the chapter to the book
            spine.append(chapter)  # Add the chapter to the spine
            toc.append(chapter)  # Add the chapter to the table of contents
        book.spine = spine
        book.toc = toc
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(output_file, book)  # Write the EPUB file to disk
        # erase any chunk files in the downloads transcriptions folder
        for file in os.listdir(os.path.join(self.download_dir, 'transcriptions')):
            if file.endswith('_chunked.txt'):
                os.remove(os.path.join(self.download_dir, 'transcriptions', file))
        return output_file

    def load_conversion_list(self, filename: str) -> None:
        """
        Load a list of files to convert.

        :param filename: Path to the file containing the list of files.
        """
        with open(filename, "r") as f:
            files = f.read().splitlines()  # Read the list of files
        self.files_root = files[0]  # First line is the root directory for the files
        self.files_to_convert = [os.path.join(self.files_root, f) for f in files[1:]]  # Remaining lines are the file paths

    def make_ebook(self) -> str:
        """
        Convert all files or YouTube videos in the download_files to a single EPUB format book.

        :return: Path to the generated EPUB file.
        """
        print("Converting files to EPUB")
        if not self.download_dir:
            print("No download directory specified. Use set_download_dir() method.")
            return ""
        else:
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)  # Create the download directory if it does not exist
        if self.download_files:
            self.download()  # Download the files if specified
        else:
            print("Add files to process using the 'add_to_files()' method.")
            return ""
        self.transcribe()  # Transcribe and redraft the files
        output_filename = os.path.join(self.download_dir, f"{self.params['title']}.epub")  # Create the output EPUB filename
        self.text_to_epub(self.rewritten_files_list, output_filename)  # Convert text files to EPUB
        return output_filename

    def estimate_cost(self, file_type: str = ".mp3") -> float:
        """
        Estimate transcription cost of all audio files in the download directory
        or all txt files in the download directory.

        :param file_type: File type to estimate cost for (default is ".mp3").
        :return: Estimated cost of transcription.
        """
        if file_type not in [".mp3", ".txt"]:
            # if file_type is neither, then just estimate the cost of the actual string
            # stored in the file_type string :)
            cost = 0
            text = file_type
            num_prompts = int(len(text.split()) / self.chunk_size)  # Estimate number of prompts
            cost += self.get_rewrite_cost(text=self.prompt * num_prompts + text)  # Add prompt cost
            cost += self.get_rewrite_cost(text=text, input=False)  # Add output cost
            return cost
        cost = 0
        file_range = os.listdir(self.mp3_dir) if file_type == ".mp3" else os.listdir(self.transcriptions_dir)  # List of files in the appropriate directory

        for file in file_range:
            file = os.path.join(self.mp3_dir if file_type == ".mp3" else self.transcriptions_dir, file)
            if file.endswith(file_type):
                if file_type == ".mp3":
                    duration = self.get_audio_duration(file)  # Get the duration of the audio file
                    cost += self.get_transcription_cost(duration)  # Add transcription cost
                    number_tokens = duration * self.average_tokens_per_second  # Estimate number of tokens
                    cost += number_tokens * self.cost_per_token[self.model]['input']  # Add input token cost
                    cost += number_tokens * self.cost_per_token[self.model]['output']  # Add output token cost
                elif file_type == ".txt":
                    text = open(file, "r", encoding=self.params['encoding']).read()  # Read the text file
                    num_prompts = int(len(text.split()) / self.chunk_size)  # Estimate number of prompts
                    cost += self.get_rewrite_cost(text=self.prompt * num_prompts + text)  # Add prompt cost
                    cost += self.get_rewrite_cost(text=text, input=False)  # Add output cost
        return cost  # Return the estimated cost rounded to 2 decimal places
