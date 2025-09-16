import { Contents } from '@jupyterlab/services';

/**
 * The command IDs used by the driveBrowser plugin.
 */
export namespace CommandIDs {
  export const openDrivesDialog = 'drives:open-drives-dialog';
  export const openPath = 'drives:open-path';
  export const toggleBrowser = 'drives:toggle-main';
  export const createNewDrive = 'drives:create-new-drive';
  export const addPublicDrive = 'drives:add-public-drive';
  export const addExternalDrive = 'drives:add-external-drive';
  export const launcher = 'launcher:create';
  export const toggleFileFilter = 'drives:toggle-file-filter';
  export const createNewDirectory = 'drives:create-new-directory';
  export const createNewFile = 'drives:create-new-file';
  export const createNewNotebook = 'drives:create-new-notebook';
  export const rename = 'drives:rename';
  export const copyPath = 'drives:copy-path';
  export const excludeDrive = 'drives:exclude-drive';
  export const includeDrive = 'drives:include-drive';
  export const copyToFilebrowser = 'drives:copy-to-filebrowser';
  export const pasteToFilebrowser = 'drives:paste-to-filebrowser';
}

/**
 * An interface that stores the drive information.
 */
export interface IDriveInfo {
  /**
   * Name of drive as stored on the provider account.
   */
  name: string;
  /**
   * Region of drive (e.g.: eu-north-1).
   */
  region: string;
  /**
   * Provider of drive (e.g.: s3, gcs).
   */
  provider: string;
  /**
   * Date drive was created.
   */
  creationDate: string;
  /**
   * Whether a content manager for the drive was already set up in the backend (true) or not (false).
   */
  mounted: boolean;
}

/**
 * An interface for storing the contents of a directory.
 */
export interface IContentsList {
  [fileName: string]: Contents.IModel;
}

/**
 * An interface that stores the registered file type, mimetype and format for each file extension.
 */
export interface IRegisteredFileTypes {
  [fileExtension: string]: {
    fileType: string;
    fileMimeTypes: string[];
    fileFormat: string;
  };
}

/**
 * Helping function to define file type, mimetype and format based on file extension.
 * @param extension file extension (e.g.: txt, ipynb, csv)
 * @returns
 */
export function getFileType(
  extension: string,
  registeredFileTypes: IRegisteredFileTypes
) {
  let fileType: string = 'text';
  let fileMimetype: string = 'text/plain';
  let fileFormat: string = 'text';

  if (registeredFileTypes[extension]) {
    fileType = registeredFileTypes[extension].fileType;
    fileMimetype = registeredFileTypes[extension].fileMimeTypes[0];
    fileFormat = registeredFileTypes[extension].fileFormat;
  }

  // the file format for notebooks appears as json, but should be text
  if (extension === '.ipynb') {
    fileFormat = 'text';
  }

  return [fileType, fileMimetype, fileFormat];
}

/**
 * Helping function to extract current drive.
 * @param path
 * @param drivesList
 * @returns current drive
 */
export function extractCurrentDrive(path: string, drivesList: IDriveInfo[]) {
  return drivesList.filter(
    x =>
      x.name ===
      (path.indexOf('/') !== -1 ? path.substring(0, path.indexOf('/')) : path)
  )[0];
}

/**
 * Helping function to eliminate drive name from path
 * @param path
 * @returns fornatted path without drive name
 */
export function formatPath(path: string) {
  return path.indexOf('/') !== -1 ? path.substring(path.indexOf('/') + 1) : '';
}
