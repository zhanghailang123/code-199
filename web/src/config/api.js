/**
 * API Configuration
 * Centralized API base URL for all fetch requests.
 * Uses environment variable in production, falls back to localhost for development.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Shared image upload handler for ByteMD editor.
 * @param {File[]} files - Files provided by the editor's uploadImages callback.
 * @returns {Promise<Array<{url: string, title: string, alt: string}>>}
 */
export async function handleUploadImages(files) {
    const uploads = await Promise.all(
        files.map(async (file) => {
            const formData = new FormData()
            formData.append('file', file)

            const res = await fetch(`${API_BASE}/api/upload`, {
                method: 'POST',
                body: formData
            })

            if (!res.ok) {
                throw new Error('Upload failed')
            }

            const data = await res.json()
            return {
                url: data.url,
                title: file.name,
                alt: file.name
            }
        })
    )
    return uploads
}
