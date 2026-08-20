# The old subdomain's redirect

This is the entire contents of the Cloudflare Pages project
`chronoscape-timeline`, which used to serve the site at
`chronoscape.charlietrenorden.com`.

The site moved to `charlietrenorden.com/chronoscape/` on 20/08/2026. Rather than
delete the project - which would have left the old URL dead instead of pointing
somewhere - it now serves nothing but a redirect:

```
/*  https://charlietrenorden.com/chronoscape/:splat  301
```

`_redirects` does the work, for every path including `sitemap.xml` and
`robots.txt`, so there is exactly one indexable copy of the site. `index.html`
is a fallback for anything that reads the body rather than the status line,
since a static file at `/` takes precedence over a `_redirects` rule.

It is checked in so the redirect is reproducible rather than existing only as a
one-off upload. To rebuild it:

```bash
npx wrangler pages deploy tools/subdomain-redirect --project-name chronoscape-timeline
```

**Never point that command at `site/dist`.** That would put a second complete
copy of the site back on the subdomain, each copy declaring itself canonical,
which is the state this replaced.
