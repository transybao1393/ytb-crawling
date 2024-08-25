import yt_dlp as youtube_dl


# TODO: Download all video information list
def download_youtube_video_info(video_url, save_subtitles=True, save_comments=True, lang="en"):
    # Options for downloading video information
    ydl_opts = {
        'ratelimit': '100K',              # Limit download speed to 100KB/s
        'writeinfojson': True,            # Download video info as JSON
        'writesubtitles': save_subtitles, # Download subtitles if available
        'subtitleslangs': [lang],         # Specify the subtitle language
        'subtitlesformat': 'srt',         # Download subtitles in SRT format
        'skip_download': True,            # Don't download the actual video
        'outtmpl': f'%(title)s.%(ext)s',  # Template for saving files
    }

    # Download video info, title, description, and subtitles
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        title = info_dict.get('title', 'Unknown Title')
        description = info_dict.get('description', 'No description available.')
        subtitles = info_dict.get('requested_subtitles', {})
        comment_count = info_dict.get('comment_count', 'No comments available.')

        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"Subtitle Language(s) Available: {list(subtitles.keys()) if subtitles else 'No subtitles available.'}")
        print(f"Comment Count: {comment_count}")

    # Optionally, download comments separately
    if save_comments:
        download_youtube_comments(video_url)

def download_youtube_comments(video_url, save_as="comments.json"):
    # Download YouTube comments using yt-dlp
    ydl_opts = {
        'ratelimit': '100K',             # Limit download speed to 100KB/s
        'writeinfojson': True,           # Save video info as JSON
        'skip_download': True,           # Skip video download
        'outtmpl': save_as,              # Save comments in JSON format
    }
    
    print(f"Downloading comments for {video_url}...")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            comments = info.get('comments', 'No comments available.')
            with open(save_as, 'w') as f:
                f.write(comments)
                print(f"Comments saved as {save_as}")
        except Exception as e:
            print(f"Error downloading comments: {e}")

def download_youtube_subtitles(video_url, language="en", save_as="subtitles.srt"):
    # Options for youtube-dl
    ydl_opts = {
        'writesubtitles': True,  # Enable subtitle download
        'ratelimit': '100K',  # Limit download speed to 100KB/s
        # 'subtitleslangs': ['en'],  # Specify subtitle language
        'skip_download': True,  # Do not download the video itself
        'subtitlesformat': 'srt',  # Download subtitles in SRT format
        'outtmpl': save_as,  # Save the subtitles with the specified filename
        'listsubs': True, # List available subtitles that supported by Yourube
        'writeautomaticsub': True,  # This option enables auto-generated subtitles
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            subtitles = info_dict.get('subtitles', {})
            if subtitles:
                print("Available subtitles:")
                for lang in subtitles.keys():
                    print(f"- {lang}")
                    # check if if en/vi/ja is available => if yes => download
                    if lang == 'en' or lang == 'vi' or lang == 'ja':
                        ydl.download([video_url])  # Download the subtitles
            else:
                print("No subtitles available for this video.")
            
            print(f"Subtitles saved as {save_as}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # video_url = 'https://www.youtube.com/watch?v=8iuLXODzL04' # Japanese song, Tabun
    video_url = 'https://www.youtube.com/watch?v=7p5jQwzCf0Y' # English song, Golden Hour
    
    # youtube video subtitles
    download_youtube_subtitles(video_url, language='en', save_as="subtitles.srt")

    # youtube video information
    # download_youtube_video_info(video_url, save_subtitles=True, save_comments=True, lang='en')
