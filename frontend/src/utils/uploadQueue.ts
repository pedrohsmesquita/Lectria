/**
 * Upload Queue Manager using IndexedDB
 * Persists video files and upload state across browser sessions
 */
import { openDB, DBSchema, IDBPDatabase } from 'idb';

// ============================================
// Database Schema
// ============================================

interface UploadQueueDB extends DBSchema {
    videos: {
        key: string;
        value: {
            id: string;
            bookId: string;
            file: File;
            status: 'pending' | 'uploading' | 'success' | 'error';
            progress: number;
            error?: string;
            addedAt: number;
        };
    };
}

const DB_NAME = 'lectria-upload-queue';
const DB_VERSION = 1;
const STORE_NAME = 'videos';

// ============================================
// Database Connection
// ============================================

let dbPromise: Promise<IDBPDatabase<UploadQueueDB>> | null = null;

const getDB = async (): Promise<IDBPDatabase<UploadQueueDB>> => {
    if (!dbPromise) {
        dbPromise = openDB<UploadQueueDB>(DB_NAME, DB_VERSION, {
            upgrade(db) {
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                }
            },
        });
    }
    return dbPromise;
};

// ============================================
// Queue Operations
// ============================================

export interface VideoQueueItem {
    id: string;
    bookId: string;
    file: File;
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

/**
 * Add video to upload queue
 */
export const addToQueue = async (
    bookId: string,
    file: File
): Promise<VideoQueueItem> => {
    const db = await getDB();

    const item = {
        id: Math.random().toString(36).substring(7),
        bookId,
        file,
        status: 'pending' as const,
        progress: 0,
        addedAt: Date.now()
    };

    await db.add(STORE_NAME, item as any);

    return {
        id: item.id,
        bookId: item.bookId,
        file: item.file,
        status: item.status,
        progress: item.progress
    };
};

/**
 * Get all videos in queue for a specific book
 */
export const getQueueForBook = async (bookId: string): Promise<VideoQueueItem[]> => {
    const db = await getDB();
    const allItems = await db.getAll(STORE_NAME);

    return allItems
        .filter(item => item.bookId === bookId)
        .map(item => ({
            id: item.id,
            bookId: item.bookId,
            file: item.file,
            status: item.status,
            progress: item.progress,
            error: item.error
        }));
};

/**
 * Get all pending/uploading videos across all books
 */
export const getPendingUploads = async (): Promise<VideoQueueItem[]> => {
    const db = await getDB();
    const allItems = await db.getAll(STORE_NAME);

    return allItems
        .filter(item => item.status === 'pending' || item.status === 'uploading')
        .map(item => ({
            id: item.id,
            bookId: item.bookId,
            file: item.file,
            status: item.status,
            progress: item.progress,
            error: item.error
        }));
};

/**
 * Update video status in queue
 */
export const updateVideoStatus = async (
    id: string,
    status: 'pending' | 'uploading' | 'success' | 'error',
    progress: number = 0,
    error?: string
): Promise<void> => {
    const db = await getDB();
    const item = await db.get(STORE_NAME, id);

    if (item) {
        item.status = status;
        item.progress = progress;
        if (error) item.error = error;
        await db.put(STORE_NAME, item);
    }
};

/**
 * Remove video from queue
 */
export const removeFromQueue = async (id: string): Promise<void> => {
    const db = await getDB();
    await db.delete(STORE_NAME, id);
};

/**
 * Clear all completed/errored videos from queue
 */
export const clearCompleted = async (bookId?: string): Promise<void> => {
    const db = await getDB();
    const allItems = await db.getAll(STORE_NAME);

    const toDelete = allItems.filter(item => {
        const matchesBook = bookId ? item.bookId === bookId : true;
        return matchesBook && (item.status === 'success' || item.status === 'error');
    });

    for (const item of toDelete) {
        await db.delete(STORE_NAME, item.id);
    }
};

/**
 * Clear entire queue
 */
export const clearAllQueue = async (): Promise<void> => {
    const db = await getDB();
    await db.clear(STORE_NAME);
};
