// _worker.js

const CDN_URL = "https://cdn.mistahub.in";
const DEFAULT_TITLE = "MistaHub - Premium App Store";
const DEFAULT_DESC = "Discover the best apps, AI tools, and games.";
const DEFAULT_IMAGE = "https://cdn-icons-png.flaticon.com/512/1041/1041916.png";

const BOT_AGENTS = [
    'facebookexternalhit', 'whatsapp', 'telegrambot', 
    'twitterbot', 'linkedinbot', 'discordbot', 'googlebot'
];

// Check if the request is from a social media bot
function isBot(userAgent) {
    if (!userAgent) return false;
    const ua = userAgent.toLowerCase();
    return BOT_AGENTS.some(bot => ua.includes(bot));
}

// Fix relative image URLs to absolute CDN URLs
function fixImageUrl(url) {
    if (!url) return DEFAULT_IMAGE;
    url = url.trim();
    if (url.startsWith('http') || url.startsWith('data:')) return url;
    return `${CDN_URL}/${url.replace(/^\/+/, '')}`;
}

// Strip HTML tags from rich text descriptions
function stripHtml(html) {
    if (!html) return '';
    return html.replace(/<[^>]*>?/gm, '').substring(0, 150) + '...';
}

export default {
    async fetch(request, env) {
        const url = new URL(request.url);
        const userAgent = request.headers.get('User-Agent') || '';
        const path = url.pathname;

        // ==========================================
        // 1. BOT HANDLING (For WhatsApp/Telegram Previews)
        // ==========================================
        if (isBot(userAgent)) {
            let title = DEFAULT_TITLE;
            let desc = DEFAULT_DESC;
            let image = DEFAULT_IMAGE;
            let type = "website";

            try {
                if (path.startsWith('/app/')) {
                    const id = path.split('/')[2];
                    const res = await fetch(`${CDN_URL}/store.js`);
                    const apps = await res.json();
                    const app = apps.find(a => a.id == id);
                    if (app) {
                        title = `${app.name} - Free Download | MistaHub`;
                        desc = stripHtml(app.about) || DEFAULT_DESC;
                        image = fixImageUrl(app.icon);
                    }
                } 
                else if (path.startsWith('/blog/')) {
                    const id = path.split('/')[2];
                    const res = await fetch(`${CDN_URL}/blog.json`);
                    const blogs = await res.json();
                    const blog = blogs.find(b => b.id == id);
                    if (blog) {
                        title = `${blog.title} | MistaHub`;
                        desc = stripHtml(blog.content) || DEFAULT_DESC;
                        image = fixImageUrl(blog.image);
                        type = "article";
                    }
                } 
                else if (path.startsWith('/page/')) {
                    const id = path.split('/')[2];
                    title = `${id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} - MistaHub`;
                }

                // Return Raw HTML strictly for the Bot to read meta tags
                const botHtml = `<!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>${title}</title>
                    <meta name="description" content="${desc}">
                    <meta property="og:title" content="${title}">
                    <meta property="og:description" content="${desc}">
                    <meta property="og:image" content="${image}">
                    <meta property="og:url" content="${request.url}">
                    <meta property="og:type" content="${type}">
                    <meta name="twitter:card" content="summary_large_image">
                    <meta name="twitter:title" content="${title}">
                    <meta name="twitter:description" content="${desc}">
                    <meta name="twitter:image" content="${image}">
                </head>
                <body>
                    <h1>${title}</h1>
                    <img src="${image}" alt="Preview Image" />
                    <p>${desc}</p>
                </body>
                </html>`;

                return new Response(botHtml, {
                    headers: { 'Content-Type': 'text/html;charset=UTF-8' },
                });

            } catch (error) {
                console.error("Bot Fetch Error:", error);
                // If fetch fails, it falls back to DEFAULT_TITLE, etc. (handled in template)
            }
        }

        // ==========================================
        // 2. NORMAL USER HANDLING (SPA Routing)
        // ==========================================
        try {
            // Fetch the requested asset (like CSS, JS, or index.html)
            let response = await env.ASSETS.fetch(request);
            
            // If the URL is something like /app/123, Cloudflare won't find a file named "123".
            // It will return 404. We catch this and serve 'index.html' instead!
            if (response.status === 404) {
                const indexRequest = new Request(new URL('/', request.url), request);
                return await env.ASSETS.fetch(indexRequest);
            }
            
            return response;
        } catch (e) {
            return new Response("Error loading page", { status: 500 });
        }
    }
};
