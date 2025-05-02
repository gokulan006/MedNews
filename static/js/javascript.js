const JSON_URL = "/static/articles.json";

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

async function fetchArticles() {
    const container = document.getElementById('articles-container');
    container.innerHTML = '<div class="loading">Loading articles...</div>';
    
    try {
        const response = await fetch(JSON_URL);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const articles = await response.json();
        
        if (articles.length === 0) {
            container.innerHTML = '<div class="empty">No articles found.</div>';
            return;
        }
        
        container.innerHTML = '';
        articles.forEach(article => {
            const articleCard = document.createElement('div');
            articleCard.className = 'article-card';
            
            // Create truncated text
            const shortText = truncateText(article.article_text, 500);
            const fullText = article.article_text;
            
            articleCard.innerHTML = `
                <h2>${article.headline}</h2>
                <p class="summary">${shortText}</p>
                <div class="meta">
                    <span>Published: ${article.published_date}</span>
                    <button class="read-more">Read more</button>
                    <a href="${article.link}" target="_blank" class="original-link">Original Article</a>
                </div>
            `;
            
            // Add click handler for Read more button
            const readMoreBtn = articleCard.querySelector('.read-more');
            const summaryEl = articleCard.querySelector('.summary');
            
            readMoreBtn.addEventListener('click', () => {
                if (summaryEl.textContent === shortText) {
                    summaryEl.textContent = fullText;
                    readMoreBtn.textContent = 'Read less';
                } else {
                    summaryEl.textContent = shortText;
                    readMoreBtn.textContent = 'Read more';
                }
            });
            
            container.appendChild(articleCard);
        });
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load articles. Please try again later.</div>';
        console.error('Error fetching articles:', error);
    }
}

document.addEventListener('DOMContentLoaded', fetchArticles);