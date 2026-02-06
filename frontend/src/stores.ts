import { writable } from 'svelte/store';

export const databaseName = writable<string>('fec');
