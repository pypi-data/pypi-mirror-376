import React from 'react';
import { useNavigate } from 'react-router';
import { default as log } from '@/logger';

import type { FileOrFolder, FileSharePath, Result } from '@/shared.types';
import {
  getFileBrowsePath,
  makeMapKey,
  sendFetchRequest,
  makeBrowseLink
} from '@/utils';
import { useCookiesContext } from './CookiesContext';
import { useZoneAndFspMapContext } from './ZonesAndFspMapContext';
import { normalizePosixStylePath } from '@/utils/pathHandling';
import { createSuccess, handleError, toHttpError } from '@/utils/errorHandling';

type FileBrowserResponse = {
  info: FileOrFolder;
  files: FileOrFolder[];
};

type FileBrowserContextProviderProps = {
  children: React.ReactNode;
  fspName: string | undefined;
  filePath: string | undefined;
};

interface FileBrowserState {
  currentFileSharePath: FileSharePath | null;
  currentFileOrFolder: FileOrFolder | null;
  files: FileOrFolder[];
  propertiesTarget: FileOrFolder | null;
  selectedFiles: FileOrFolder[];
  uiErrorMsg: string | null;
  fileContentRefreshTrigger: number;
}

type FileBrowserContextType = {
  fileBrowserState: FileBrowserState;
  fspName: string | undefined;
  filePath: string | undefined;

  areFileDataLoading: boolean;
  refreshFiles: () => Promise<Result<void>>;
  triggerFileContentRefresh: () => void;
  handleLeftClick: (
    file: FileOrFolder,
    showFilePropertiesDrawer: boolean
  ) => void;
  updateFilesWithContextMenuClick: (file: FileOrFolder) => void;
  setCurrentFileSharePath: (sharePath: FileSharePath | null) => void;
};

const FileBrowserContext = React.createContext<FileBrowserContextType | null>(
  null
);

export const useFileBrowserContext = () => {
  const context = React.useContext(FileBrowserContext);
  if (!context) {
    throw new Error(
      'useFileBrowserContext must be used within a FileBrowserContextProvider'
    );
  }
  return context;
};

// fspName and filePath come from URL parameters, accessed in MainLayout
export const FileBrowserContextProvider = ({
  children,
  fspName,
  filePath
}: FileBrowserContextProviderProps) => {
  // Unified state that keeps a consistent view of the file browser
  const [fileBrowserState, setFileBrowserState] =
    React.useState<FileBrowserState>({
      currentFileSharePath: null,
      currentFileOrFolder: null,
      files: [],
      propertiesTarget: null,
      selectedFiles: [],
      uiErrorMsg: null,
      fileContentRefreshTrigger: 0
    });
  const [areFileDataLoading, setAreFileDataLoading] = React.useState(false);

  // Function to update fileBrowserState with complete, consistent data
  const updateFileBrowserState = React.useCallback(
    (newState: Partial<FileBrowserState>) => {
      log.debug('Updating fileBrowserState:', newState);
      setFileBrowserState(prev => ({
        ...prev,
        ...newState
      }));
    },
    []
  );

  // Function to update all states consistently
  const updateAllStates = React.useCallback(
    (
      sharePath: FileSharePath | null,
      fileOrFolder: FileOrFolder | null,
      fileList: FileOrFolder[],
      targetItem: FileOrFolder | null,
      selectedItems: FileOrFolder[] = [],
      msg: string | null
    ) => {
      // Update fileBrowserState with complete, consistent data
      updateFileBrowserState({
        currentFileSharePath: sharePath,
        currentFileOrFolder: fileOrFolder,
        files: fileList,
        propertiesTarget: targetItem,
        selectedFiles: selectedItems,
        uiErrorMsg: msg
      });
    },
    [updateFileBrowserState]
  );

  const setCurrentFileSharePath = React.useCallback(
    (sharePath: FileSharePath | null) => {
      updateFileBrowserState({
        currentFileSharePath: sharePath
      });
    },
    [updateFileBrowserState]
  );

  const { cookies } = useCookiesContext();
  const { zonesAndFileSharePathsMap, isZonesMapReady } =
    useZoneAndFspMapContext();
  const navigate = useNavigate();

  const handleLeftClick = (
    // e: React.MouseEvent<HTMLDivElement>,
    file: FileOrFolder,
    // displayFiles: FileOrFolder[],
    showFilePropertiesDrawer: boolean
  ) => {
    // If clicking on a file (not directory), navigate to the file URL
    if (!file.is_dir && fileBrowserState.currentFileSharePath) {
      const fileLink = makeBrowseLink(
        fileBrowserState.currentFileSharePath.name,
        file.path
      );
      navigate(fileLink);
      return;
    }

    // For directories, handle selection as before
    // if (e.shiftKey) {
    //   // If shift key held down while clicking,
    //   // add all files between the last selected and the current file
    //   const lastSelectedIndex = selectedFiles.length
    //     ? displayFiles.findIndex(
    //         f => f === selectedFiles[selectedFiles.length - 1]
    //       )
    //     : -1;
    //   const currentIndex = displayFiles.findIndex(f => f.name === file.name);
    //   const start = Math.min(lastSelectedIndex, currentIndex);
    //   const end = Math.max(lastSelectedIndex, currentIndex);
    //   const newSelectedFiles = displayFiles.slice(start, end + 1);
    //   setSelectedFiles(newSelectedFiles);
    //   setPropertiesTarget(file);
    // } else if (e.metaKey) {
    //   // If  "Windows/Cmd" is held down while clicking,
    //   // toggle the current file in the selection
    //   // and set it as the properties target
    //   const currentIndex = selectedFiles.indexOf(file);
    //   const newSelectedFiles = [...selectedFiles];

    //   if (currentIndex === -1) {
    //     newSelectedFiles.push(file);
    //   } else {
    //     newSelectedFiles.splice(currentIndex, 1);
    //   }

    //   setSelectedFiles(newSelectedFiles);
    //   setPropertiesTarget(file);
    // } else {
    // If no modifier keys are held down, select the current file
    const currentIndex = fileBrowserState.selectedFiles.indexOf(file);
    const newSelectedFiles =
      currentIndex === -1 ||
      fileBrowserState.selectedFiles.length > 1 ||
      showFilePropertiesDrawer
        ? [file]
        : [];
    const newPropertiesTarget =
      currentIndex === -1 ||
      fileBrowserState.selectedFiles.length > 1 ||
      showFilePropertiesDrawer
        ? file
        : null;

    updateAllStates(
      fileBrowserState.currentFileSharePath,
      fileBrowserState.currentFileOrFolder,
      fileBrowserState.files,
      newPropertiesTarget,
      newSelectedFiles,
      fileBrowserState.uiErrorMsg
    );
  };

  const updateFilesWithContextMenuClick = (file: FileOrFolder) => {
    // Update file selection - if file is not already selected, select it; otherwise keep current selection
    // if (fileBrowserState.selectedFiles.length === 0) {
    //   updateAllStates(
    //     fileBrowserState.currentFileSharePath,
    //     fileBrowserState.currentFolder,
    //     fileBrowserState.files,
    //     file, // Set as properties target
    //     [file], // Select the clicked file
    //     fileBrowserState.uiErrorMsg
    //   );
    //   return;
    // }

    const currentIndex = fileBrowserState.selectedFiles.indexOf(file);
    const newSelectedFiles =
      currentIndex === -1 ? [file] : [...fileBrowserState.selectedFiles];

    updateAllStates(
      fileBrowserState.currentFileSharePath,
      fileBrowserState.currentFileOrFolder,
      fileBrowserState.files,
      file, // Set as properties target
      newSelectedFiles,
      fileBrowserState.uiErrorMsg
    );
  };

  // Function to fetch files for the current FSP and current folder
  const fetchFileInfo = React.useCallback(
    async (
      fspName: string,
      folderName: string
    ): Promise<FileBrowserResponse> => {
      const url = getFileBrowsePath(fspName, folderName);

      const response = await sendFetchRequest(url, 'GET', cookies['_xsrf']);
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 403) {
          if (data.info && data.info.owner) {
            throw new Error(
              `You do not have permission to list this folder. Contact the owner (${data.info.owner}) for access.`
            );
          } else {
            throw new Error(
              'You do not have permission to list this folder. Contact the owner for access.'
            );
          }
        } else if (response.status === 404) {
          throw new Error('Folder not found');
        } else {
          throw await toHttpError(response);
        }
      }

      return data as FileBrowserResponse;
    },
    [cookies]
  );

  // Fetch metadata for the given FSP and path, and update the fileBrowserState
  const fetchAndUpdateFileBrowserState = React.useCallback(
    async (fsp: FileSharePath, targetPath: string): Promise<void> => {
      setAreFileDataLoading(true);
      log.debug(
        'Fetching metadata for FSP:',
        fsp.name,
        'and path:',
        targetPath
      );
      let fileOrFolder: FileOrFolder | null = null;

      try {
        // Fetch the metadata for the target path
        const response = await fetchFileInfo(fsp.name, targetPath);
        fileOrFolder = response.info as FileOrFolder;

        if (fileOrFolder) {
          fileOrFolder = {
            ...fileOrFolder,
            path: normalizePosixStylePath(fileOrFolder.path)
          };
        }

        // Normalize the file paths in POSIX style, assuming POSIX-style paths
        // For files, response.files will be empty array or undefined
        let files = (response.files || []).map(file => ({
          ...file,
          path: normalizePosixStylePath(file.path)
        })) as FileOrFolder[];

        // Sort: directories first, then files; alphabetically within each type
        files = files.sort((a: FileOrFolder, b: FileOrFolder) => {
          if (a.is_dir === b.is_dir) {
            return a.name.localeCompare(b.name);
          }
          return a.is_dir ? -1 : 1;
        });

        // Update all states consistently
        // If it's a file, it becomes both the current item and the properties target
        const propertiesTarget = fileOrFolder;
        const selectedFiles = fileOrFolder ? [fileOrFolder] : [];

        updateAllStates(
          fsp,
          fileOrFolder,
          files,
          propertiesTarget,
          selectedFiles,
          null
        );
      } catch (error) {
        log.error(error);
        if (error instanceof Error) {
          updateAllStates(
            fsp,
            fileOrFolder,
            [],
            fileOrFolder,
            [],
            error.message
          );
        } else {
          updateAllStates(
            fsp,
            fileOrFolder,
            [],
            fileOrFolder,
            [],
            'An unknown error occurred'
          );
        }
      } finally {
        setAreFileDataLoading(false);
      }
    },
    [updateAllStates, fetchFileInfo]
  );

  // Function to refresh files for the current FSP and current file or folder
  const refreshFiles = async (): Promise<Result<void>> => {
    if (
      !fileBrowserState.currentFileSharePath ||
      !fileBrowserState.currentFileOrFolder
    ) {
      return handleError(
        new Error('File share path and file/folder required to refresh')
      );
    }
    log.debug('Refreshing file list');
    try {
      await fetchAndUpdateFileBrowserState(
        fileBrowserState.currentFileSharePath,
        fileBrowserState.currentFileOrFolder.path
      );
      return createSuccess(undefined);
    } catch (error) {
      return handleError(error);
    }
  };

  // Function to trigger a refresh of file content in FileViewer
  const triggerFileContentRefresh = React.useCallback(() => {
    log.debug('Triggering file content refresh');
    setFileBrowserState(prev => ({
      ...prev,
      fileContentRefreshTrigger: prev.fileContentRefreshTrigger + 1
    }));
  }, []);

  // Effect to update currentFolder and propertiesTarget when URL params change
  React.useEffect(() => {
    log.debug('URL changed: fspName=', fspName, 'filePath=', filePath);
    let cancelled = false;
    const updateCurrentFileSharePathAndFolder = async () => {
      if (!isZonesMapReady || !zonesAndFileSharePathsMap || !fspName) {
        if (cancelled) {
          return;
        }
        updateAllStates(
          null,
          null,
          [],
          null,
          [],
          'Invalid file share path name'
        );
        return;
      }

      const fspKey = makeMapKey('fsp', fspName);
      const urlFsp = zonesAndFileSharePathsMap[fspKey] as FileSharePath;
      if (!urlFsp) {
        log.error(`File share path not found for fspName: ${fspName}`);
        if (cancelled) {
          return;
        }
        updateAllStates(
          null,
          null,
          [],
          null,
          [],
          'Invalid file share path name'
        );
        return;
      }

      await fetchAndUpdateFileBrowserState(urlFsp, filePath || '.');

      if (cancelled) {
        return;
      }
    };
    updateCurrentFileSharePathAndFolder();
    return () => {
      // Cleanup function to prevent state updates if a dependency changes
      // in an asynchronous operation
      cancelled = true;
    };
  }, [
    isZonesMapReady,
    zonesAndFileSharePathsMap,
    fspName,
    filePath,
    updateAllStates,
    fetchAndUpdateFileBrowserState
  ]);

  return (
    <FileBrowserContext.Provider
      value={{
        fileBrowserState,
        fspName,
        filePath,
        refreshFiles,
        triggerFileContentRefresh,
        handleLeftClick,
        updateFilesWithContextMenuClick,
        areFileDataLoading,
        setCurrentFileSharePath
      }}
    >
      {children}
    </FileBrowserContext.Provider>
  );
};
