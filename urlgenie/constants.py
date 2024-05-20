import re

#-Regex patterns-#
email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.[a-z]{2,63}", flags = re.IGNORECASE)
email_pattern = re.compile(r"[a-z0-9#%$*!][a-z0-9.#$!_%+-]+@[a-z0-9.-]+\.(?!png|jpg|gif|bmp|jpeg)[a-z]{2,63}", flags = re.IGNORECASE)
contact_pattern = lambda href, url : re.search(rf"{re.escape(url)}.*(?:contact|reach|support)", href, flags = re.IGNORECASE)
phone_pattern_loose = re.compile(r"\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:,\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})*", flags = re.IGNORECASE)
phone_pattern_strict = re.compile(r"\+\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:,\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})*", flags = re.IGNORECASE)
twitter_handle_1 = re.compile(r"(?:x|twitter).com/+@?[a-z0-9_]{1,20}", flags = re.IGNORECASE)
twitter_handle_2 = re.compile(r"(?:x|twitter).com[^~]{1,50}screen_name=@?[a-z0-9_]{1,20}", flags = re.IGNORECASE)
facebook_id = re.compile(
    r"(?:fb|facebook).com[^~]{1,50}(?:"r"(?:\?|&|profile.php|group.php)"
    r"(?:id=|gid=|ref=name&id=)|[a-z0-9%-]{2,}-|/|__user=|"
    r"\?set=a.(?:[0-9.]+)?)[0-9]{5,}", flags = re.IGNORECASE)
facebook_handle = re.compile(
    r"(?:fb|facebook).com(?:.br|.au)?/+(?:#!/|#1/)?"
    r"(?:pg/|watch/|groups/|events/|\.\.\./|pages/category/(?:photographer|journalist)/|"
    r"home.php[#!\?]{1,3}/|\?[a-z_]{1,}=[a-z_#!?]{1,}/|pages/edit/\?id=\d+#!/|\?_rdr#!/)?"
    r"@?[a-z0-9%.-]{1,50}", flags = re.IGNORECASE)
linkedin_id = re.compile(
    r"linkedin.com[^~]{1,50}(?:gid=|groupid=|"
    r"gr(?:ou)?ps/|company-beta/|edu/|organization/|edu/school\?id=)"
    r"(?:[a-z0-9&%.~_-]{2,200})?[0-9]{2,10}", flags = re.IGNORECASE)
linkedin_handle = re.compile(
    r"linkedin.com(?:.br|.au)?/+(?:organization-guest/)?"
    r"(?:(?:in/|company/|showcase/|school/|companies/|profile/view\?id=)"
    r"(?:acwaa[a-z0-9_-]{34}|[a-z0-9&%.~_-]{2,200})|"
    r"pub/[a-z0-9&%.~_-]{2,150}/[a-z0-9]{1,3}/[a-z0-9]{1,3}/[a-z0-9]{1,3})", flags = re.IGNORECASE)
instagram_handle = re.compile(
    r"instagram.com(?:.br|.au)?/+(?:accounts/login/\?next=/)"
    r"?[a-z0-9_.]{1,30}", flags = re.IGNORECASE)

#-A pattern dictionary for href mailto and tel search-#
primary_patterns = {
    "phone": [phone_pattern_loose],
    "email": [email_pattern],
}

#-A pattern dictionary for universal search-#
generic_patterns = {
    "phone": [phone_pattern_strict],
    "email": [email_pattern],
    "instagram": [instagram_handle],
    "facebook": [facebook_id, facebook_handle],
    "linkedin": [linkedin_id, linkedin_handle],
    "twitter": [twitter_handle_1, twitter_handle_2],
}
