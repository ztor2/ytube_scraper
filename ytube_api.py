# pip install --upgrade google-api-python-client
# pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2
# pip install oauth2client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
import time
import db_model

class ytube_api():
    def __init__(self):
        self.db_model = db_model.DB_model()

    def scraper(self, keyword, vid_num, comment_num):
        developer_key = 'API_Key'
        api_name = "youtube"
        api_ver = "v3"
        youtube = build(api_name, api_ver, developerKey=developer_key)
        search_response = youtube.search().list(q=keyword,
                                                order="date",
                                                part="snippet",
                                                maxResults=vid_num).execute()

        vids = []
        comments = []
        for i in search_response['items']:
            vid = {}
            vid_id = i['id']['videoId']
            stats = youtube.videos().list(part="statistics", id=vid_id).execute()
            vid['platform'] = 1
            vid['id'] = vid_id
            vid['title'] = i['snippet']['title']
            vid['channel'] = i['snippet']['channelTitle']
            vid['description'] = i['snippet']['description']
            vid['viewCount'] = stats['items'][0]['statistics']['viewCount']
            try:
                vid['likeCount'] = stats['items'][0]['statistics']['likeCount']
            except KeyError:
                vid['likeCount'] = 0
            vid['commentCount'] = stats['items'][0]['statistics']['commentCount']
            vid['date'] = i['snippet']['publishTime'].replace('T', ' ').replace('Z', '')
            vids.append(vid)

            request = youtube.commentThreads().list(part="snippet", videoId=vid_id, order="orderUnspecified")
            response = request.execute()
            items = response["items"][:comment_num]
            for j in items:
                comment = {}
                comment_info = j["snippet"]["topLevelComment"]["snippet"]
                comment['id'] = j['id']
                comment['platform'] = 1
                comment['vidTitle'] = i['snippet']['title']
                comment['user'] = comment_info["authorDisplayName"]
                comment['content'] = comment_info["textDisplay"]
                comment['likeCount'] = comment_info["likeCount"]
                comment['date'] = comment_info['publishedAt'].replace('T', ' ').replace('Z', '')
                comments.append(comment)

        return vids, comments

    def insert_db(self, keyword, vids, comments):
        for idx, i in enumerate(vids):
            vid_data_db = {'unique_id': i['id'],
                               'keyword': keyword,
                               'title': i['title'],
                               'user_id': 0,
                               'user_name': i['channel'],
                               'posting_date': i['date'],
                               'view_count': i['viewCount'],
                               'like_count': i['likeCount'],
                               'dislike_count': 0,
                               'contents': i['description'],
                               'user_follow': 0,
                               'user_follower': 0,
                               'user_medias': 0,
                               'comment_count': i['commentCount'],
                               'additional_data': []
                               }
            vid_isnew = self.db_model.set_data_body(1, vid_data_db)
            self.db_model.set_data_body_info(1, vid_isnew['is_new'], vid_data_db)

        for idx, j in enumerate(comments):
            vid_comment_data_db = {'unique_id': j['id'],
                                       'keyword': keyword,
                                       'comment_id': j['vidTitle'],
                                       'user_name': j['user'],
                                       'comment': self.addslashes(j['content']),
                                       'comment_like': int(j['likeCount']),
                                       'comment_date': (j['date']),
                                       }
            self.db_model.set_data_comment(1, vid_comment_data_db, vid_isnew['is_new'], vid_isnew['last_time_update'])

        row_id = self.db_model.set_daily_log(keyword, 1)
        self.db_model.set_daily_log('', '', row_id)

    def addslashes(self, strings):
        d = {'"': '\\"', "'": "\\'", "\0": "\\\0", "\\": "\\\\"}
        return ''.join(d.get(i, i) for i in strings)


if __name__ == "__main__":
    keyword = input('keyword: ')
    vid_num = int(input('video num: '))
    comment_num = int(input('comment num: '))

    start = time.time()
    ytube = ytube_api()
    vids, comments = ytube.scraper(keyword, vid_num, comment_num)
    print('vid count:', len(vids), 'comment count:', len(comments))
    ytube.insert_db(keyword, vids, comments)
    elapsed = time.time() - start
    mnt, sec = divmod(elapsed, 60)
    print('Finished!', '\nElapsed time: {}m {}s'.format(int(mnt), int(sec)))