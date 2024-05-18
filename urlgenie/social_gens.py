import re
from urllib.parse import urlparse, unquote

def pub_to_in(url: str) -> str :

    path_list = urlparse(url).path.split('/')
    path_list[5] = f'0{path_list[5]}' if len(path_list[5]) == 2 else f'00{path_list[5]}' if len(path_list[5]) == 1 else path_list[5]
    path_list[4] = f'0{path_list[4]}' if len(path_list[4]) == 2 else f'00{path_list[4]}' if len(path_list[4]) == 1 else path_list[4]
    final_url = f'linkedin.com/in/{path_list[2]}-{path_list[5]}{path_list[4]}{path_list[3]}'

    return final_url


def facebook_gen(url: str, subdomain: str, get_handle: bool, keep_periods: bool, bad_social: str) -> str :

    url = url.lower()

    id = re.search(r"/user/[0-9]{5,}(\/|&|\?|\.\.\.|#|$|http|=)", url, re.IGNORECASE)

    if not id:
        id = re.search(r"((\?|&|profile.php|group.php)(id=|gid=)|[a-z0-9%-]{2,}-|/|profile.php\?ref=name&id=|__user=|\?set=a.([0-9.]+)?)[0-9]{5,}(\/|&|\?|\.\.\.|#|$|http|=)", url, re.IGNORECASE)

    if id:
        id = id[0].split('.')[-1]

        id = re.sub("[^0-9]","",id)

        return f"https://{subdomain}.facebook.com/{id}" if not get_handle else id

    handle = re.search(f"https://{subdomain}." + r"facebook.com(.br|.au)?/(/)?(#!/|#1/)?people/@?[a-z0-9%.]{1,50}(\/|\?|#|$|#|http|=)", url, re.IGNORECASE)

    if not handle:
        handle = re.search(f"https://{subdomain}." + r"facebook.com(.br|.au)?/(/)?(#!/|#1/)?(pg/|watch/|groups/|events/|\.\.\./|pages/category/(photographer|journalist)/|home.php[#!\?]{1,3}/|\?[a-z_]{1,}=[a-z_#!?]{1,}/|pages/edit/\?id=\d+#!/|\?_rdr#!/)?@?[a-z0-9%.-]{1,50}(\/|\?|#|$|#|http|=)", url, re.IGNORECASE)

    if handle:
        exceptions = ['profilephp', 'groupid', 'groups', 'people', 'pg', 'pages', 'homephp', 'public', 'events', 'watch', 'homephp!', 'media', 'dialog', 'help', 'search', 'sharer', 'sharerphp', 'login', '2008']
        handle = handle[0][:-1] if handle[0][-1] in ['/', '?', '#', '=', '&'] else handle[0]
        handle = handle[:-4].split('/') if handle[-4:] == 'http' else handle.split('/')
        subdir = handle[-2]
        handle = handle[-1].replace('@','') if keep_periods else handle[-1].replace('@','').replace(".", "")
        handle = f"{subdir}/{handle}" if subdir in ['groups'] and handle not in exceptions else handle
        if handle and handle.replace('.', '').lower() not in exceptions:
            return f"https://{subdomain}.facebook.com/{handle}" if not get_handle else handle

    return bad_social if bad_social else url


def instagram_gen(url: str, subdomain: str, get_handle: bool, bad_social: str) -> str :

    url = url.lower()

    handle = re.search(f"https://{subdomain}." + r"instagram.com(.br|.au)?/(/)?(accounts/login/\?next=/)?[a-z0-9_.]{1,30}(\/|&|\?|#|$|http|=)", url, re.IGNORECASE)
    if handle:
        handle = handle[0][:-1] if handle[0][-1] in ['/', '?', '#', '=', '&'] else handle[0]
        handle = handle[:-4] if handle[-4:] == 'http' else handle
        handle = handle.split('/')[-1]
        if handle.lower() not in ['p', 'accounts', 'explore']:
            return f"https://{subdomain}.instagram.com/{handle}" if not get_handle else handle

    return bad_social if bad_social else url


def twitter_gen(url: str, subdomain: str, get_handle: bool, bad_social: str) -> str :

    url = url.lower()

    handle = re.search(r"screen_name=@?[a-z0-9_.]{1,20}(\/|&|\?|\[|#|$|http|=)", url, re.IGNORECASE)

    if not handle:
        handle = re.search(f"https://{subdomain}." + r"twitter.com/(/)?@?[a-z0-9_.]{1,20}(\/|&|\?|\[|#|$|http|=)", url, re.IGNORECASE)

    if handle:
        handle = handle[0].split('screen_name=')[-1]
        handle = handle[:-1] if handle[-1] in ['/', '?', '#', '[', '=', '&'] else handle
        handle = handle[:-4] if handle[-4:] == 'http' else handle
        handle = handle.split('/')[-1].replace('@','')

        if handle.lower() not in ["i", "home", "share", "intent"]:
            return f"https://twitter.com/{handle}" if not get_handle else handle

    return bad_social if bad_social else url


def linkedin_gen(url: str, subdomain: str, get_handle: bool, subdirs: dict, bad_social: str) -> str :

    handle = re.search(f"https://{subdomain}." + r"linkedin.com(.br|.au)?/(/)?in/(ACwAA|acwaa)[A-Za-z0-9_-]{34}(\/|&|\?|#|$|http|=)", url, re.IGNORECASE)

    if not handle:
        url = url.lower()
        handle = re.search(f"https://{subdomain}." + r"linkedin.com(.br|.au)?/(/)?(organization-guest/)?((in/|company/|showcase/|school/|companies/|profile/view\?id=)[a-z0-9&%.~_-]{2,200}|(gr(ou)?ps/|company-beta/|edu/|organization/|(edu/school\?id=)?)([a-z0-9&%.~_-]{2,200})?[0-9]{2,10})(\/|&|\?|#|$|http|=)", url, re.IGNORECASE)
    if not handle:
        handle = re.search(f"https://{subdomain}." + r"linkedin.com(.br|.au)?/(/)?pub/[a-z0-9&%.~_-]{2,150}/[a-z0-9]{1,3}/[a-z0-9]{1,3}/[a-z0-9]{1,3}(\/|&|\?|#|$|http|=)", url, re.IGNORECASE)
        if handle:
            handle = [pub_to_in(handle[0])]

    if handle:
        handle = handle[0][:-1] if handle[0][-1] in ['/', '?', '#', '=', '&'] else handle[0]
        handle = handle[:-4] if handle[-4:] == 'http' else handle
        handle = handle[:-4].split('/') if handle[-4:] == 'http' else handle.split('/')
        subdir = next((key for key, value in subdirs.items() if handle[-2] in value), handle[-2])
        handle = handle[-1] if subdir not in ['groups', 'edu'] else re.sub(r"[^0-9]", "", handle[-1])
        handle = handle.replace('view?id=', '') if subdir in ['profile', 'in'] else handle

        if len(unquote(handle)) < 101 and subdir not in ['www.linkedin.com'] and handle.lower() not in ['company-beta']:
            return f"https://{subdomain}.linkedin.com/{subdir}/{handle}" if not get_handle else handle
        else:
            handle = None

    if not handle:
        id = re.search(r"(\?|&|/)(gid=|groupid=)[0-9]{2,}(\/|&|\?|\.\.\.|#|$|http|=)", url, re.IGNORECASE)

    if id:
        id = re.sub("[^0-9]","",id[0])
        return f"https://{subdomain}.linkedin.com/groups/{id}" if not get_handle else id

    return bad_social if bad_social else url