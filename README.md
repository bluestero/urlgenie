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
### Importing and creating object
Let's first import the package and create an object of it to access its features.

```python
from urlgenie import  UrlGenie

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

This can be achieved using the flags (boolean parameters) and it would be explained here: [flags.md](https://github.com/bluestero/urlgenie/blob/main/flags.md).

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
```

This would return:
![url-extraction]("./images/mascot.png")


## ⭐ Love It? [Star It!](https://github.com/bluestero/urlgenie)
Just a simple click but would mean a lot to me.