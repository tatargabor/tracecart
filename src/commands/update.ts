import { cmdInit } from './init.js';

export async function cmdUpdate(args: string[], pkgRoot: string): Promise<void> {
  await cmdInit(args, pkgRoot);
}
