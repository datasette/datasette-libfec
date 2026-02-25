import { writable, derived } from 'svelte/store';

export const databaseName = writable<string>('');
export const basePath = derived(databaseName, ($db) => ($db ? `/${$db}/-/libfec` : ''));
export const apiBasePath = derived(databaseName, ($db) => ($db ? `/${$db}/-/api/libfec` : ''));
