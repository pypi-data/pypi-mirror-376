pattern = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'url': r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*',
    'ipv4': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'credit_card': r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    'social_security': r'\b\d{3}-\d{2}-\d{4}\b',
    'hashtag': r'#\w+',
    'mention': r'@\w+',
    'price': r'\$\d+(?:\.\d{2})?',
    'date': r'\b\d{4}-\d{2}-\d{2}\b',
    'time': r'\b\d{1,2}:\d{2}(?::\d{2})?\b'
}

file_type = {
    'html': 'html',
    'css': 'css',
    'javascript': 'js',
    'image': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'ico'],
    'document': ['pdf', 'doc', 'docx', 'txt', 'rtf'],
    'media': ['mp3', 'mp4', 'avi', 'mov', 'wav', 'webm'],
    'archive': ['zip', 'rar', 'tar', 'gz', '7z'],
    'font': ['woff', 'woff2', 'ttf', 'otf', 'eot']
}