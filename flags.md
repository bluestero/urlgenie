## ♨️ URL Genie Flags
URL Genie takes URL as an input, validates it, identifies the components of the URL (if valid), and processes it according to the set flags.

Below are the flags you can use to adjust the generalization according to your use case.

We will be using the following input value to explain the flags: `facebook.com/some...Handle?some=query#someFragment////`

### lower
- False by default.
- If True, returns the URL in lower.
- `https://www.facebook.com/some...handle`

### keep_path
- True by default.
- If False, will return the url without the path.
- `https://www.facebook.com` (www is being added due to replace_social_subdomain flag).

### keep_query
- False by default.
- If True, preserves the query.
- `https://www.facebook.com/some...Handle?some=query`

### get_handle
- False by default.
- If True, returns the social handle (would work only when replace_social_subdomain flag is True).
- `some...handle`

### get_domain
- False by default.
- If True, will return only the domain.
- `facebook`

### keep_periods
- True by default.
- If False, will remove the periods from the facebook handle.
- `somehandle`

### keep_fragment
- False by default.
- If True, preserves the fragment.
- `https://www.facebook.com/some...handle`

### comma_separated
- False by default. Let's use `facebook.com/handle1,, , facebook.com/handle2` as an example.
- If True, will separate the input by comma and recursively run the generalize function on it with the given flags.
- `https://www.facebook.com/handle1, https://www.facebook.com/handle2`

### replace_empty_subdomain
- False by default.
- If True, will add www as default subdomain if empty.
- `https://www.facebook.com/some...handle`

### get_domain_with_tld
- False by default.
- If True, returns the domain along with its TLD.
- `facebook.com`

### social_rectification
- True by default.
- If False, will not run customized social validation and generalization.
- `https://www.facebook.com/some...Handle`

### replace_all_subdomain
- False by default.
- If True, will replace the subdomain with www.
- `https://www.facebook.com/some...handle`

### replace_social_subdomain
- True by default.
- If False, will not replace the empty / valid social subdomain with www.
- `https://www.facebook.com/some...handle` (Will still replace social subdomain if social_rectification is True).

That's it! Now you can set these flags according to your use-cases and enhance your data-driven projects!

Happy coding!