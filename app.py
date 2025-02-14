import streamlit as st
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import pandas as pd

# Set up YouTube API client
API_KEY = os.getenv('AIzaSyC9Cf0P61P-g7IRpa1wB7NT4bR6qrQmEqg')
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_stats(video_id):
    request = youtube.videos().list(
        part="statistics,contentDetails",
        id=video_id
    )
    response = request.execute()
    return response['items'][0]['statistics'], response['items'][0]['contentDetails']

def get_channel_stats(channel_id):
    request = youtube.channels().list(
        part="statistics,snippet",
        id=channel_id
    )
    response = request.execute()
    return response['items'][0]['statistics'], response['items'][0]['snippet']

def search_videos(keywords, start_date, end_date, min_subs, max_subs, result_limit, video_type):
    videos = []
    
    for keyword in keywords:
        request = youtube.search().list(
            q=keyword.strip(),
            part="snippet",
            type="video",
            publishedAfter=start_date.isoformat() + "Z",
            publishedBefore=end_date.isoformat() + "Z",
            maxResults=result_limit,
            order="viewCount"
        )
        response = request.execute()
        
        for item in response['items']:
            video_id = item['id']['videoId']
            channel_id = item['snippet']['channelId']
            
            video_stats, video_details = get_video_stats(video_id)
            channel_stats, channel_snippet = get_channel_stats(channel_id)
            
            subscriber_count = int(channel_stats.get('subscriberCount', 0))
            if min_subs <= subscriber_count <= max_subs:
                duration = video_details['duration']
                is_short = 'PT60S' >= duration
                
                if (video_type == 'All' or 
                    (video_type == 'Shorts' and is_short) or 
                    (video_type == 'Long' and not is_short)):
                    
                    videos.append({
                        'title': item['snippet']['title'],
                        'video_id': video_id,
                        'channel_name': item['snippet']['channelTitle'],
                        'thumbnail': item['snippet']['thumbnails']['high']['url'],
                        'views': int(video_stats.get('viewCount', 0)),
                        'subscribers': subscriber_count,
                        'published_at': item['snippet']['publishedAt'],
                        'channel_created': channel_snippet['publishedAt'],
                        'duration': duration,
                        'is_short': is_short
                    })
    
    return videos

# Streamlit UI
st.title("YouTube Trending Videos Analyzer")
st.write("Find trending videos from smaller channels")

# Sidebar for filters
st.sidebar.title("Filters")

keywords_input = st.sidebar.text_input(
    "Enter keywords (comma-separated)",
    placeholder="gaming, technology, cooking..."
)

date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=7), datetime.now()),
    max_value=datetime.now()
)

min_subs, max_subs = st.sidebar.slider(
    "Channel Subscriber Count",
    min_value=100,
    max_value=10000,
    value=(100, 10000)
)

result_limit = st.sidebar.slider(
    "Number of Results",
    min_value=10,
    max_value=50,
    value=20
)

video_type = st.sidebar.selectbox(
    "Video Type",
    options=["All", "Shorts", "Long"]
)

if st.sidebar.button("Research"):
    if keywords_input and len(date_range) == 2:
        keywords = [k.strip() for k in keywords_input.split(',')]
        start_date, end_date = date_range
        
        with st.spinner('Searching for videos...'):
            videos = search_videos(keywords, start_date, end_date, min_subs, max_subs, result_limit, video_type)
            
            if videos:
                df = pd.DataFrame(videos)
                df['published_at'] = pd.to_datetime(df['published_at'])
                df['channel_created'] = pd.to_datetime(df['channel_created'])
                df = df.sort_values('views', ascending=False)
                
                for _, video in df.iterrows():
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.image(video['thumbnail'], use_column_width=True)
                    
                    with col2:
                        st.markdown(f"### [{video['title']}](https://youtube.com/watch?v={video['video_id']})")
                        st.write(f"Channel: {video['channel_name']}")
                        st.write(f"Views: {video['views']:,}")
                        st.write(f"Subscriber Count: {video['subscribers']:,}")
                        st.write(f"Published: {video['published_at'].strftime('%Y-%m-%d')}")
                        st.write(f"Channel Created: {video['channel_created'].strftime('%Y-%m-%d')}")
                        st.write(f"Duration: {video['duration']}")
                        st.write(f"Video Type: {'Short' if video['is_short'] else 'Long'}")
                    
                    st.divider()
            else:
                st.warning("No videos found matching your criteria.")
    else:
        st.error("Please enter keywords and select a valid date range.")

# Add footer with instructions
st.sidebar.markdown("""
---
### How to use:
1. Enter keywords related to your research
2. Set the date range for video publication
3. Adjust the channel subscriber count range
4. Choose the number of results to display
5. Select the video type (All, Shorts, or Long)
6. Click "Research" to find trending videos
""")
