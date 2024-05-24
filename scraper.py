import requests
import json
import time

s = requests.session()

headers={"X-Transaction-Source": "Interface=Web,Interface-Name=SD,Interface-Type=Service Portal,Interface-SysID=09dafa4287ca31100e3552cabbbb35f8", "X-Use-Polaris": "false", "X-UserToken": None, "x-portal": "09dafa4287ca31100e3552cabbbb35f8"}

# cookies={"JSESSIONID": "DDC91980B4AD2289FE961B55F44D2C40", "glide_user_route": "glide.5fb1092f6a5979d6d0a4309da399d872", "glide_language": "it"}

def init_session(topic_id):
    # init cookies
    s.get("https://servicedesk.unitn.it/sd/it/home")
    # extract X-UserToken
    r = s.get("https://servicedesk.unitn.it/sd/it/topic", params={"id": "unitrento_v2_topic", "topic_id": topic_id})
    
    user_token = r.text.split("var g_ck = '")[1][:72]
    headers={"X-Transaction-Source": "Interface=Web,Interface-Name=SD,Interface-Type=Service Portal,Interface-SysID=09dafa4287ca31100e3552cabbbb35f8", "X-Use-Polaris": "false", "X-UserToken": user_token, "x-portal": "09dafa4287ca31100e3552cabbbb35f8"}
    s.headers.update(headers)
    print(s.headers)
    
def next_service_cards(prev_data, topic_id):
    # payload = prev_data['result']['containers'][2]['rows'][0]['columns'][0]['widgets'][0]['widget']['data']
    payload = prev_data
    payload.update({
        "getNext": False,
        "aisFilterBy": "",
        "aisSortBy": "",
        "action": "show-more",
        "sessionRotationTrigger": True,
    })

    r = s.post("https://servicedesk.unitn.it/api/now/sp/rectangle/1986c42233ca71109976923fad5c7b17", params={"id": "unitrento_v2_topic", "topic_id": topic_id}, json=payload)

    print(r.ok)

    if r.ok:
        data = json.loads(r.text)
        serviceCards = []
        for content in data['result']['data']['content']:
            content = content['widgetData']['data']['catalogCardData']
            serviceCard = {'title': content['title'], 'sysId': content['sysId'], 'url': content['url']}
            serviceCards.append(serviceCard)
            # print(serviceCard)
        return serviceCards, data['result']['data']


def get_service_cards(topic_id):
    r = s.get("https://servicedesk.unitn.it/api/now/sp/page", params={"id": "unitrento_v2_topic", "topic_id": topic_id, "time": "1716456455653", "portal_id": "09dafa4287ca31100e3552cabbbb35f8", f"request_uri": "%2Fsd%3Fid%3Dunitrento_v2_topic%26topic_id%3D{topic_id}", "omitTheme": "true"})
    # print(r.text)
    if r.ok:
        data = json.loads(r.text)
        serviceCards = []
        for content in data['result']['containers'][2]['rows'][0]['columns'][0]['widgets'][0]['widget']['data']['content']:
            content = content['widgetData']['data']['widgetData']['options']
            serviceCard = {'title': content['title'], 'sysId': content['sysId'], 'url': content['url']}
            serviceCards.append(serviceCard)
            # print(serviceCard)
        return serviceCards, data['result']['containers'][2]['rows'][0]['columns'][0]['widgets'][0]['widget']['data']

def get_service_articles(sysId):
    r = s.get("https://servicedesk.unitn.it/api/now/sp/page", params={"id": "unitrento_v2_service_card_article", "sys_id": f"{sysId}", "time": "1716467756857", "portal_id": "09dafa4287ca31100e3552cabbbb35f8", "request_uri": f"%2Fsd%3Fid%3Dunitrento_v2_service_card_article%26sys_id%3D{sysId}", "omitTheme": "true"})

    # print(r.text)

    if r.ok:
        data = json.loads(r.text)
        articles = []
        for k,section_articles in data['result']['containers'][1]['rows'][0]['columns'][0]['widgets'][0]['widget']['data'].items():
            if type(section_articles) != type([]) or len(section_articles) == 0:
                continue
            for content in section_articles:
                article = {'name': content['name'], 'number': content['number'], 'link': content['link']}
                articles.append(article)
                # print(article)
        return articles
    
def get_article_content(sysparm_article):
    r = s.get("https://servicedesk.unitn.it/api/now/sp/page", params={"id": "unitrento_v2_kb_article", "sysparm_article": sysparm_article, "time": "1716469049141", "portal_id": "09dafa4287ca31100e3552cabbbb35f8", "request_uri": f"%2Fsd%3Fid%3Dunitrento_v2_kb_article%26sysparm_article%3D{sysparm_article}", "omitTheme": "true"})
    
    # print(r.text)

    if r.ok:
        data = json.loads(r.text)
        data = data['result']['containers'][1]['rows'][0]['columns'][0]['widgets'][0]['widget']['data']
        article = {
            'page_title': data['page_title'],
            'sys_updated_on': data['sys_updated_on'],
            'number': data['number'],
            'kbContentData': data['kbContentData'],
            'kbName': data['kbName'],
        }
        # print(article['page_title'])
        # print(article['kbContentData']['data'])
        return article


def scrape_by_topic(topic_id):
    init_session(topic_id)
    
    serviceCards, response_data = get_service_cards(topic_id)
    print(len(serviceCards))
    showMore = response_data['showMore']
    while showMore:
        newServiceCards, response_data = next_service_cards(response_data, topic_id)
        serviceCards += newServiceCards
        showMore = response_data['showMore']
        print(len(serviceCards))
    
    for sc in serviceCards:
        # print('###########################################################################')
        # print(f"get_service_articles '{sc['title']}'")
        sc['articles'] = get_service_articles(sc['sysId'])
        # print(sc['articles'])
        # input('>>>>>>>>>>>>>>>>>>>>> press enter: ')

        for article in sc['articles']:
            article['content'] = get_article_content(article['number'])
            # print(article['content'])
            # input('>>>>>>>>>>>>>>>>>>>>> press enter: ')
    
    # print(json.dumps(serviceCards, sort_keys=True, indent=2))
    return serviceCards

def main():
    topic_ids = {
        "Biblioteca": "dcb54a8a87c631100e3552cabbbb3539",
        "Didattica": "99f112f233ea35109976923fad5c7bd2",
        "Ricerca": "f64256f233ea35109976923fad5c7b1d",
        "Risorse umane": "c26256f233ea35109976923fad5c7b09",
        "Governance": "19b256f233ea35109976923fad5c7b84",
        "ICT": "98a50a8a87c631100e3552cabbbb35f3",
    }

    topics = []
    for name, topic_id in topic_ids.items():
        serviceCards = scrape_by_topic(topic_id)
        topics.append({"topic": name, "serviceCards": serviceCards})

    with open("data.json", "w") as fp:
        json.dump(topics, sort_keys=True, indent=2, fp=fp)


if __name__ == '__main__':
    main()
