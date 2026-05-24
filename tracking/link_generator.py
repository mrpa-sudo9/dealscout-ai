from urllib.parse import urlencode, urlparse, urlunparse


class LinkGenerator:
    def generate(self, base_url: str, affiliate_tag: str, source: str = "dealscout") -> str:
        parsed = urlparse(base_url)
        existing_params = dict(p.split("=") for p in parsed.query.split("&")) if parsed.query else {}
        existing_params.update({
            "ref": affiliate_tag,
            "utm_source": source,
            "utm_medium": "affiliate",
            "utm_campaign": "dealscout_ai",
        })
        new_parsed = parsed._replace(query=urlencode(existing_params))
        return urlunparse(new_parsed)
