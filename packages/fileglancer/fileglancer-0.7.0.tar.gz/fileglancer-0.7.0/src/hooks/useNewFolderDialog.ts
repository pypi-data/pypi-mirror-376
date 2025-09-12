import React from 'react';

import { getFileBrowsePath, sendFetchRequest, joinPaths } from '@/utils';
import { handleError, toHttpError } from '@/utils/errorHandling';
import { useFileBrowserContext } from '@/contexts/FileBrowserContext';
import { useCookiesContext } from '@/contexts/CookiesContext';
import type { Result } from '@/shared.types';

export default function useNewFolderDialog() {
  const [newName, setNewName] = React.useState<string>('');

  const { fileBrowserState, refreshFiles } = useFileBrowserContext();
  const { currentFileOrFolder, currentFileSharePath } = fileBrowserState;
  const { cookies } = useCookiesContext();

  async function handleNewFolderSubmit(): Promise<Result<void>> {
    if (!currentFileSharePath) {
      return handleError(new Error('No file share path selected.'));
    }
    if (!currentFileOrFolder) {
      return handleError(new Error('No current file or folder selected.'));
    }
    try {
      const response = await sendFetchRequest(
        getFileBrowsePath(
          currentFileSharePath.name,
          joinPaths(currentFileOrFolder.path, newName)
        ),
        'POST',
        cookies['_xsrf'],
        {
          type: 'directory'
        }
      );
      if (response.ok) {
        return await refreshFiles();
      } else {
        if (response.status === 403) {
          return handleError(new Error('Permission denied'));
        } else {
          throw toHttpError(response);
        }
      }
    } catch (error) {
      return handleError(error);
    }
  }

  return {
    handleNewFolderSubmit,
    newName,
    setNewName
  };
}
