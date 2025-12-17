// This acts as a "Database" for Phase 1
// It uses Vite's string import feature to load all Markdown files at build/runtime

// Load all markdown files from the content directory
// ?raw tells Vite to import the content as a string
const modules = import.meta.glob('../../../content/**/*.md', { as: 'raw', eager: true })

export function getAllContent() {
    const content = []
    for (const path in modules) {
        const fileContent = modules[path]
        // Simple frontmatter parsing (we can improve this later or use a library)
        // For now, let's just use the filename as ID if frontmatter fails

        // Extract ID from filename
        // path example: ../../../content/questions/2024-math-q01.md
        const parts = path.split('/')
        const filename = parts[parts.length - 1]
        const id = filename.replace('.md', '')
        const type = parts.includes('questions') ? 'question' :
            parts.includes('knowledge_base') ? 'knowledge' : 'other'

        // Basic category/subject detection
        let subject = 'unknown'
        if (path.includes('math')) subject = 'math'
        else if (path.includes('logic')) subject = 'logic'
        else if (path.includes('english')) subject = 'english'

        content.push({
            id,
            path,
            type,
            subject,
            raw: fileContent // The raw markdown string
        })
    }
    return content
}

export function getContentById(id) {
    const all = getAllContent()
    return all.find(item => item.id === id)
}
