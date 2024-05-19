<p align = "center">
<img src = "./images/mascot.png" alt = "urlgenie" /><div align = "center" style = "margin-top: 0;">
<h1>🧞 URL Genie 🧞</h1>
</div>
<h3 align="center">
  URL extraction, generalization, validation, and filtration made easy.
</h3>

## 🚀 About URL Genie
It is a python package based on research involving over 2 million URLs, designed to handle URLs in a flexible manner for data-driven projects.

## 💡 How it works
It checks the given URL input, validates it against the URL regex, identifies each component of the URL and processes it according to the set flags.

## ✨ Features
- Handle both encoded and decoded URLs.
- Filter out valid, invalid URLs and also bad socials with ease.
- Extract Email and Socials from a given text and validate them.
- URL validation using regex and over 1400 TLDs (off by default).
- Duplicate reduction by minimizing the general and social URL patterns.
- Domain mismatch by just extracting the domain along with the TLD and match against the email domain.
- Researched and refined social regexes to recognize different social patterns and generalizes them to the standardized format.

## ⚙️ Installation
First things first, you need to install URL Genie by running the following command in your terminal:

```shell
python -m pip install urlgenie
```

That's it! Now you can use URL Genie in your code.

## ♨️ Usage
### Importing and creating the object
Let's first import the package and create an object of it to access its features.

```python
from urlgenie import  UrlGenie
from pprint import pprint

genie = UrlGenie()
```

### Generalizing your first URL
Let's try to give a sample input url and get it generalized.

```python
url = "test.something.com/hello?somequery=True#someFragment"
gen = genie.generalize(url)
print(gen)
```

Would return `https://test.something.com/hello` as the output.

It detects that the schema is missing and adds it. By default, it removes the query (starts with ?) and fragment (starts with #).

### Different flags for generalization
As explained previously, URL Genie breaks down the URL, identifies the components and allows you to form the URL as per your needs.

This can be achieved using the flags (boolean parameters) and is explained here: [flags.md](https://github.com/bluestero/urlgenie/blob/main/flags.md).

## ❗ For Nerds
Below are the different use cases where URL Genie might come in handy.

### URL Extraction
Just provide a string text and URL Genie will extract a dict containing emails and socials for you.

```python
text = """
This is a good email: sample@gmail.com and this is a bad email: sample@image.png.
Another would be an email with a custom domain: sample@example.com.
Sample facebook facebook.com/sample1, lets try with fb domain: fb.com/sample2.
Lets add a bad facebook: fb.com/profile.php?
Lets add 2 twitter formats: x.com/sample and twitter.com/sample with same handles.
How about a linkedin pub? linkedin.com/pub/aravind-p-r/24/324/185?_l=en_US.
Let's also add its in url: linkedin.com/in/aravind-p-r-18532424/"""
result_dict = genie.extract_from_text(text)
pprint(result_dict)
```

This would return:

```shell
{'email': {'sample@example.com', 'sample@gmail.com'},
 'facebook': {'fb.com/sample2.', 'facebook.com/sample1', 'fb.com/profile.php'},
 'instagram': set(),
 'linkedin': {'linkedin.com/in/aravind-p-r-18532424', 'linkedin.com/pub/aravind-p-r/24/324/185'},
 'phone': set(),
 'twitter': {'x.com/sample', 'twitter.com/sample'}}
```

### Extract Validation
As you can see, it has strict regexes which prevented the bad email (sample@image.png) from being extracted.

But it has extracted fb.com/profile.php which is not really a URL we want since it does not lead to any person / organization / page.

Also, there are duplicates for twitter having the same handle and are not really in a standardized format.

For that, we can validate the given extract to remove invalid data and standardize the valid ones.

```python
result_dict = genie.extract_from_text(text)
validated_dict = genie.validate_result_dict(result_dict)
pprint(validated_dict)
```

This would return:

```shell
{'email': {'sample@example.com', 'sample@gmail.com'},
 'facebook': {'https://www.facebook.com/sample1', 'https://www.facebook.com/sample2.'},
 'instagram': set(),
 'linkedin': {'https://www.linkedin.com/in/aravind-p-r-18532424'},
 'phone': set(),
 'twitter': {'https://twitter.com/sample'}}
```

With this, we have removed the duplicates, invalid URLs like fb.com/profile.php, generalized URLs such as LinkedIn PUB to IN.

### Email Domain Validation
When you scrape websites for contact info, you might get a lot of emails, and not all of them would be related to the organization.

To filter out the ones which are not related to the organization, we can use the email validation.

```python
result_dict = genie.extract_from_text(text)
validated_dict = genie.validate_result_dict(result_dict, url = "https://www.example.com/ContactUs")
pprint(validated_dict)
```

This would return:

```shell
{'email': {'sample@example.com'},
 'facebook': {'https://www.facebook.com/sample1', 'https://www.facebook.com/sample2.'},
 'instagram': set(),
 'linkedin': {'https://www.linkedin.com/in/aravind-p-r-18532424'},
 'phone': set(),
 'twitter': {'https://twitter.com/sample'}}
```

Now, we have removed the sample@gmail.com which is not related to the organization's URL we have provided.

This would prove to be helpful when making scrapers or processing and cleaning data.

### Social Filtration
You can filter out valid URLs, invalid URLs and invalid socials when you have data in bulk to deal with.

For this example, we would be using data stored in a CSV.

**Test.CSV**

```csv
url
badbadwebsite?!,something
fb.com/people/hello
twitter.com/intent
https://x.com/intent/follow?original_referer=&region=follow_link&screen_name=elonmusk&tw_p=followbutton&variant=2&mx=2
anotherbadwebsite???
```

**Test.py***

```python
import pandas as pd
from pprint import pprint
from urlgenie import  UrlGenie

#-Reading the CSV-#
df = pd.read_csv("test.csv", encoding = "utf-8")

#-Creating UrlGenie object with custom texts for Bad Url and Socials, and TLD validation-#
genie = UrlGenie(bad_url = "Bad Url", bad_social = "Bad Social", proper_tlds = True)

#-Applying the generalize function and creating a new column-#
df["gen"] = df["url"].apply(genie.generalize)

#-Printing the updated dataframe-#
pprint(df)
```

Would return:

```
                                                 url                             gen
0                                    badbadwebsite?!                         Bad Url
1                                fb.com/people/hello  https://www.facebook.com/hello
2                                 twitter.com/intent                      Bad Social
3                                random.haz/somePath                         Bad Url
4  https://x.com/intent/follow?original_referer=&...    https://twitter.com/elonmusk
5                               anotherbadwebsite???                         Bad Url
```

As you can see, we got genrealized URLs for the valid ones and Bad Url, Bad Social for the invalid ones.

The reason why random.haz was deemed as invalid is due to the proper_tlds flag which verified the tld 'haz' agaisnt over 1400 TLDs.

As for the twitter one, intent is not a valid twitter page, hence a valid url but an invalid social.

## 📖 Resources
- [Sample Sheet](https://docs.google.com/spreadsheets/d/12QHwZxiDv80ksFngQK10hkOmPQLRpI0s6dPfe6mRuxk/edit?usp=sharing)
- [Social Research Doc](https://docs.google.com/document/d/12Z025x5m9xBlEahkiRI0wLE0zJNhPtSTCllk_GIqReQ/edit?usp=sharing)

## ⭐ Love It? [Star It!](https://github.com/bluestero/urlgenie)
Just a simple click but would help me out ;)
