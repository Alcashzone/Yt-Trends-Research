import streamlit as st
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import pandas as pd

# Set up YouTube API client
API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_stats(video_id):
    """Get video statistics including view count"""
    request = youtube.videos().list(
        part="statistics",
        id=video_id
    )
    response = request.execute()
    return response['items'][0]['statistics']

def get_channel_stats(channel_id):
    """Get channel statistics including subscriber count"""
    request = youtube.channels().list(
        part="statistics",
        id=channel_id
    )
    response = request.execute()
    return response['items'][0]['statistics']

def search_videos(keywords):
    # Calculate date 7 days ago
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    videos = []
    
    # Search for each keyword
    for keyword in keywords:
        request = youtube.search().list(
            q=keyword.strip(),
            part="snippet",
            type="video",
            publishedAfter=seven_days_ago,
            maxResults=10,
            order="viewCount"
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']['videoId']
            channel_id = item['snippet']['channelId']
            
            # Get video statistics
            video_stats = get_video_stats(video_id)
            # Get channel statistics
            channel_stats = get_channel_stats(channel_id)
            
            # Only include videos from channels with relatively fewer subscribers
            # but good view counts (customize these thresholds as needed)
            if (int(channel_stats['subscriberCount']) < 100000 and 
                int(video_stats['viewCount']) > 10000):
                
                videos.append({
                    'title': item['snippet']['title'],
                    'video_id': video_id,
                    'channel_name': item['snippet']['channelTitle'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'views': int(video_stats['viewCount']),
                    'subscribers': int(channel_stats['subscriberCount']),
                    'published_at': item['snippet']['publishedAt']
                })
    
    return videos

# Streamlit UI
st.title("YouTube Trending Videos Analyzer")
st.write("Find videos from the last 7 days with high views but from smaller channels")

# Input box for keywords
keywords_input = st.text_input(
    "Enter keywords (comma-separated)",
    placeholder="gaming, technology, cooking..."
)

if st.button("Research"):
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(',')]
        
        with st.spinner('Searching for videos...'):
            videos = search_videos(keywords)
            
            if videos:
                # Convert to DataFrame and sort by views
                df = pd.DataFrame(videos)
                df = df.sort_values('views', ascending=False)
                
                # Display results
                for _, video in df.iterrows():
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.image(video['thumbnail'], use_column_width=True)
                    
                    with col2:
                        st.markdown(f"### [{video['title']}](https://youtube.com/watch?v={video['video_id']})")
                        st.write(f"Channel: {video['channel_name']}")
                        st.write(f"Views: {video['views']:,}")
                        st.write(f"Subscriber Count: {video['subscribers']:,}")
                        st.write(f"Published: {video['published_at']}")
                    
                    st.divider()
            else:
                st.warning("No videos found matching your criteria.")
    else:
        st.error("Please enter at least one keyword.")

# Add footer with instructions
st.markdown("""
---
### How to use:
1. Enter keywords related to your research, separated by commas
2. Click "Research" to find trending videos
3. Results will show videos from the last 7 days with:
   - High view counts (>10,000 views)
   - From smaller channels (<100,000 subscribers)
""")