import os
import re
import sys
import json
import pandas as pd
from tldextract import extract
from urllib.parse import urlparse, quote, unquote
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import constants, social_gens


class UrlGenie():

    def __init__(self, proper_tlds: bool = False, bad_url = "", bad_social = "") -> None:

        #--Creating bad social and bad url objects--#
        self.bad_url = bad_url
        self.bad_social = bad_social

        #--Storing the package directory inside an object--#
        self.dir = os.path.dirname(os.path.realpath(__file__)) + '//'

        #--Getting list of all valid TLDs and joining them to use in url regex--#
        with open(os.path.join(self.dir + "TLDs.txt"), "r", encoding = "utf-8") as file:
            self.tlds = "|".join([line.strip() for line in file]) if proper_tlds else "[A-Za-z]{2,4}"

        #--Checking if subdomain file exists--#
        if os.path.exists(self.dir + 'subdomains.json'):
            with open(self.dir + 'subdomains.json', 'r', encoding = 'utf-8') as config:
                self.subdomains = json.load(config)

        else:        
            #--Creating skeleton of the subdomain dictionary to fetch subdomains and invalid social URLs--#
            self.subdomains = {
                'facebook' : [],
                'twitter' : [],
                'linkedin' : [],
                'instagram' : []
                }

        #--Initializing Domains dictionary from the config--#
        with open(self.dir + 'config.json', 'r', encoding = 'utf-8') as config:
            data = json.load(config)
            self.domains = data['domains']
            self.subdirs = data['subdirs']

        #--URL Validation Regex--#
        self.url_validation = re.compile(r"^((http://|https://|^)([a-z.-]{1,10}\.)*|http://|https://|^)[a-z0-9-]{1,63}\.(co.)?(" + self.tlds + ")(?=\/|$)", flags = re.IGNORECASE)

    def generalize(self,
                        url: str,
                        lower: bool = False,
                        keep_path: bool = True,
                        keep_query: bool = False,
                        get_handle: bool = False,
                        get_domain: bool = False,
                        keep_periods: bool = True,
                        keep_fragment: bool = False,
                        comma_separated: bool = False,
                        replace_empty_subdomain = False,
                        get_domain_with_tld: bool = False,
                        social_rectification: bool = True,
                        replace_all_subdomain: bool = False,
                        replace_social_subdomain: bool = True) -> str :

        if comma_separated:
            if type(url) != str:
                return url

            url_split = [self.generalize(ur.strip(), lower = lower, keep_query = keep_query, get_handle = get_handle, 
                                         get_domain = get_domain, keep_periods = keep_periods, keep_fragment = keep_fragment,
                                         replace_empty_subdomain = replace_empty_subdomain, social_rectification = social_rectification,
                                         replace_all_subdomain = replace_all_subdomain, replace_social_subdomain = replace_social_subdomain) 
                                         for ur in url.split(',') if ur.strip() != '']
            return ', '.join(url_split)

        #--Checking if the give URL is valid or not before proceeding--#
        if not bool(self.url_validation.search(str(url))):
            return self.bad_url if self.bad_url else url

        #--Encoding all the non-ASCII values--#
        url = quote(unquote(url.strip()), safe = "@%&-:?=/_.!#[]")
        url = url + '/' if url[-1] != '/' else url
        url_extract = extract(url)

        #--Changing FB to Facebook and X to Twitter--#
        url_domain = 'twitter' if social_rectification and url_extract.domain == 'x' else url_extract.domain
        url_domain = 'facebook' if social_rectification and url_extract.domain == 'fb' else url_domain

        #--Returning only the domain if get_domain is True--#
        if get_domain:
            return url_domain

        #-Returning the domain with tld if get_domain_with_tld is True-#
        if get_domain_with_tld:
            return f"{url_domain}.{url_extract.suffix}"

        #--Fixing subdomains containing extra suffixes--#
        subdomain_suffixes = ['secure', 'latest', 'cinyour', 'prod', 'm']
        fixed_subdomain = '.'.join([subdomain for subdomain in url_extract.subdomain.split('.') if subdomain not in subdomain_suffixes])

        #--Conditions for replacing subdomain with www--#
        if social_rectification:
            replace_social_subdomain = True

        conditions = [
            replace_all_subdomain,
            replace_social_subdomain and url_domain.lower() in self.domains and fixed_subdomain.lower() in self.domains[url_domain.lower()],
            replace_empty_subdomain and url_extract.subdomain == ''
        ]

        #--Replacing subdomain with www if conditions met and keeping track of other subdomains--#
        url_subdomain = 'www' if any(conditions) else url_extract.subdomain
        if replace_social_subdomain and url_subdomain != 'www':
            if url_domain.lower() in self.subdomains and url_subdomain not in self.subdomains[url_domain.lower()]:
                self.subdomains[url_domain.lower()].append(url_subdomain)

        #--Building up the URL--#
        latter = url[url.find(f'.{url_extract.suffix}/'):]
        base = f'https://{url_subdomain}.{url_domain}{latter}' if url_subdomain else f'https://{url_domain}{latter}'
        parse = urlparse(base, allow_fragments = True)
        url_query = '?' + parse.query if parse.query else ''
        url_fragment = '#' + parse.fragment if parse.fragment else ''
        url_path = f"{parse.path}{url_query}{url_fragment}" if keep_path else ""
        url = f'{parse.scheme}://{parse.netloc}{url_path}'

        #--Social function placeholders required for rectifying the social urls--#
        socials = {
            f'https://{url_subdomain}.facebook.com': lambda url: social_gens.facebook_gen(url, url_subdomain, get_handle, keep_periods, self.bad_social),
            f'https://{url_subdomain}.instagram.com': lambda url: social_gens.instagram_gen(url, url_subdomain, get_handle, self.bad_social),
            f'https://{url_subdomain}.linkedin.com': lambda url: social_gens.linkedin_gen(url, url_subdomain, get_handle, self.subdirs, self.bad_social),
            f'https://{url_subdomain}.twitter.com': lambda url: social_gens.twitter_gen(url, url_subdomain, get_handle, self.bad_social)
        }

        if social_rectification:
            for key, value in socials.items():
                if key in url.lower():
                    url = value(url)
                    return unquote(url).lower() if lower else unquote(url)

        #--Removing qury if the flag is turned off--#
        url = url.replace('?' + parse.query, '') if not keep_query else url
        url = url.replace('#' + parse.fragment, '') if not keep_fragment else url

        #--Removing ending backslashes to further standardize the url--#
        while url.endswith('/'):
            url = url[:-1]

        #--Returning the decoded url in lower if lower flag is on--#
        return unquote(url).lower() if lower else unquote(url)


    #-Function to extract emails and socials from the given text-#
    def extract_from_text(self, text: str, patterns_dict: dict = constants.generic_patterns) -> dict:

        #-Base object-#
        all_info = {
            "phone": set(),
            "email": set(),
            "facebook": set(),
            "twitter": set(),
            "linkedin": set(),
            "instagram": set(),
        }

        #-Iterating the dictionary containing different list of patterns-#
        for column, patterns in patterns_dict.items():

            #-Iterating the pattern list-#
            for pattern in patterns:

                #-Adding the regex matches in the all_info dict-#
                all_info[column] = all_info[column].union(set(pattern.findall(text)))

        #-Returning the regexed data-#
        return all_info


    #-Function to validate the result dict-#
    def validate_result_dict(self, result_dict: dict, url: str = "") -> dict:

        #-Copying the result dict instance-#
        result = result_dict.copy()

        #-Storing the original values-#
        bad_url, bad_social = self.bad_url, self.bad_social

        #-Updating the class values-#
        self.bad_url, self.bad_social = "Bad", "Bad"

        #-Function to validate emails-#
        def validate_email(emails: set) -> set:

            #-Valid emails set-#
            valid_emails = set()

            #-Iterating the emails set-#
            for email in emails:

                #-Getting the domain of the url and email-#
                url_domain = self.generalize(url, get_domain_with_tld = True)
                email_domain = email.split("@")[-1]

                #-Adding the email to the emails set if domain matches-#
                if url_domain == email_domain:
                    valid_emails.add(email)

            #-Returning the valid emails set-#
            return valid_emails

        #-Function to validate socials-#
        def validate_socials(socials: set) -> set:

            #-Valid socials set-#
            valid_socials = set()

            #-Iterating the socials set-#
            for social in socials:

                #-Generalizing the url-#
                url = self.generalize(social)

                #-Adding the social to valid socials set if valid-#
                if url != "Bad":
                    valid_socials.add(url)

            #-Returning the valid socials set-#
            return valid_socials

        #-Dict to map column names with functions-#
        validate_dict = {
            "facebook": validate_socials,
            "twitter": validate_socials,
            "linkedin": validate_socials,
            "instagram": validate_socials,
        }

        #-Adding email validation if a valid url is provided-#
        if url and self.generalize(url) != "Bad":
            validate_dict["email"] = validate_email

        #-Iterating the column name and values set of the result dict-#
        for column, values in result.items():

            #-Validating and adding the validated values if column is present-#
            if column in validate_dict:
                result[column] = validate_dict[column](values)

        #-Restoring the original values-#
        self.bad_url, self.bad_social = bad_url, bad_social

        #-Returning the validated dict-#
        return result    



    #--Function to update the json file with the newly found subdomains--#
    def update_subdomains(self):
        file_path = self.dir + "subdomains.json"
        with open(file_path, "w") as outfile:
            json.dump(self.subdomains, outfile, indent = 4)


    #--Function to retrieve the subdomains inside your calling directory--#
    def get_subdomains(self):
        file_path = os.getcwd() + "//subdomains.json"
        with open(file_path, "w") as outfile:
            json.dump(self.subdomains, outfile, indent = 4)


    #--Function to clear the subdomains dictionray--#
    def clear_subdomains(self):
        self.subdomains = {
            'facebook' : [],
            'twitter' : [],
            'linkedin' : [],
            'instagram' : []
            }
