from youtube_transcript_api import YouTubeTranscriptApi

def get_captions(video_id: str) -> str:
    """
    Retrieves the captions text for a specified video ID on youtube

    Args:
        video_id: The unique identifier for the target video (required)

    Returns:
        String containing the complete transcript text without timestamps

    Raises:
        ValueError: Raised when required 'video_id' parameter is missing
        Exception: Raised when transcript cannot be retrieved (e.g., no captions available)

    Tags:
        retrieve, transcript, text, captions
    """
    if video_id is None:
        raise ValueError("Missing required parameter 'video_id'")

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)

        transcript_text = " ".join(
            [snippet.text for snippet in transcript.snippets]
        )

        return transcript_text
    except Exception as e:
        raise Exception(
            f"Failed to retrieve transcript for video {video_id}: {str(e)}"
        )
        
def main():
    video_id = "Cr9B6yyLZSk"  # Example video ID
    captions = get_captions(video_id)
    print(captions)
    
if __name__ == "__main__":
    main()