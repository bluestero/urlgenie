from url_gen import UrlGeneralizer

gen = UrlGeneralizer()
text = "https://www.facebook.com/media/set/?set=a.874587847376.2323742.59504045&type=3#!/profile.php?id=59504045"
text = "https://www.facebook.com/skander.benmohammed/media_set?set=a.2535916286540.2132085.1512575464&type=3"
text = "https://www.facebook.com/media/set/?set=a.10216454627068860&type=3"
text = "https://www.facebook.com/media/set/?set=a.100624826695130.753.100002428381256&type=3#!/"
text = "www.twitter.com/shares"
text = "www.x.com/shares"
text = "https://www.fb.com/media/set/?set=a.100624826695130.753.100002428381256&type=3#!/"
text = "www.google.com/search?query=Ahmed+Dino"
print(gen.generalize(text, keep_query = True, keep_path = False))