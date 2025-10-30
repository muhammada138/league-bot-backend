// src/core/Metadata.ts
var Metadata = class {
  gameLength;
  lastGameChunkId;
  lastKeyFrameId;
  statsJson;
  constructor(metadata) {
    this.gameLength = metadata.gameLength;
    this.lastGameChunkId = metadata.lastGameChunkId;
    this.lastKeyFrameId = metadata.lastKeyFrameId;
    this.statsJson = JSON.parse(metadata.statsJson);
  }
  toString() {
    return JSON.stringify(this);
  }
  toBuffer() {
    return Buffer.from(this.toString());
  }
};

// src/core/ROFLReader.ts
import { existsSync, readFileSync } from "fs";

// src/parsers/Parser.ts
var Parser = class {
  data;
  /**
   * Creates a new instance of the Parser.
   * 
   * @param {Buffer} data - The data to be parsed.
   */
  constructor(data) {
    this.data = data;
  }
};

// src/parsers/new/NewROFLParser.ts
var NewROFLParser = class extends Parser {
  metadataSizeLength = 4;
  /**
   * Creates a new instance of the NewROFLParser.
   * 
   * @param {Buffer} data - The data to be parsed.
   */
  constructor(data) {
    super(data);
  }
  /**
   * Parses the data and returns the metadata of the ROFL file.
   * It locates the metadata in the data by calculating its position based on the metadata size field.
   * It then extracts the metadata, parses it as JSON, and returns it as a `Metadata` object.
   *
   * @returns {Metadata} The metadata of the ROFL file.
   */
  parse() {
    const metadataLengthPosition = this.data.length - this.metadataSizeLength;
    const metadataLength = this.data.subarray(metadataLengthPosition, this.data.length).readUInt32LE(0);
    const metadataPosition = this.data.length - metadataLength - this.metadataSizeLength;
    const rawMetadata = this.data.subarray(metadataPosition, this.data.length - this.metadataSizeLength);
    const metadata = JSON.parse(rawMetadata.toString());
    return new Metadata(metadata);
  }
};

// src/parsers/old/FileInfo.ts
var FileInfo = class {
  header;
  file;
  metadataOffset;
  metadata;
  payloadHeaderOffset;
  payloadHeader;
  payloadOffset;
  /**
   * Creates a new instance of the FileInfo.
   * 
   * @param {Buffer} data - The data to be parsed.
   */
  constructor(data) {
    this.header = data.readUInt16LE(0);
    this.file = data.readUInt32LE(2);
    this.metadataOffset = data.readUInt32LE(6);
    this.metadata = data.readUInt32LE(10);
    this.payloadHeaderOffset = data.readUInt32LE(14);
    this.payloadHeader = data.readUInt32LE(18);
    this.payloadOffset = data.readUInt32LE(22);
  }
};

// src/parsers/old/OldROFLParser.ts
var OldRoflParser = class extends Parser {
  fileInfosPosition = 262;
  fileInfosLength = 26;
  /**
   * Creates a new instance of the OldRoflParser.
   * 
   * @param {Buffer} data - The data to be parsed.
   */
  constructor(data) {
    super(data);
  }
  /**
   * Parses the data and returns the metadata of the ROFL file.
   * It first extracts the file information from the data, then uses this information to extract the metadata.
   *
   * @returns {Metadata} The metadata of the ROFL file.
   */
  parse() {
    const rawFileInfos = this.data.subarray(this.fileInfosPosition, this.fileInfosPosition + this.fileInfosLength);
    const fileInfos = new FileInfo(rawFileInfos);
    const rawMetadata = this.data.subarray(fileInfos.metadataOffset, fileInfos.payloadHeaderOffset);
    const metadata = JSON.parse(rawMetadata.toString());
    return new Metadata(metadata);
  }
};

// src/core/ROFLReader.ts
var ROFLReader = class {
  file;
  parser;
  /**
   * Creates a new instance of the ROFLReader.
   * 
   * @param {string | Buffer} pathOrBuffer - The path to the ROFL file or the file as a Buffer.
   * @throws {Error} If the file does not exist or is not a valid ROFL file.
   */
  constructor(pathOrBuffer) {
    if (Buffer.isBuffer(pathOrBuffer)) {
      this.file = pathOrBuffer;
    } else {
      if (!existsSync(pathOrBuffer))
        throw new Error(`File ${pathOrBuffer} does not exist`);
      if (!pathOrBuffer.endsWith(".rofl"))
        throw new Error(`File is not a ROFL file`);
      this.file = readFileSync(pathOrBuffer);
    }
    if (this.file.subarray(0, 4).toString() !== "RIOT")
      throw new Error(`This file is not a valid ROFL file`);
    this.parser = this.determineParser();
  }
  /**
   * Determines the appropriate parser to use based on the file version.
   * 
   * @returns {Parser} The appropriate parser.
   */
  determineParser() {
    const pattern = /^(\d{2})\.(\d{1,2})$/;
    const versionString = this.file.subarray(15, 20).toString();
    const version = versionString.endsWith(".") ? versionString.slice(0, -1) : versionString;
    const match = pattern.exec(version);
    if (!match) {
      console.error(`Version string does not match the expected pattern: ${versionString}`);
      return new OldRoflParser(this.file);
    }
    const majorVersion = parseInt(match[1], 10);
    const minorVersion = parseInt(match[2], 10);
    if (majorVersion === 14 && minorVersion === 10) {
      console.error(`This version of ROFL files is not supported: ${versionString}. Riot removed metadata in version 14.10 and reintroduced it in version 14.11.`);
      throw new Error(`Unsupported ROFL version: ${versionString}`);
    }
    if (majorVersion > 14 || majorVersion == 14 && minorVersion >= 11)
      return new NewROFLParser(this.file);
    return new OldRoflParser(this.file);
  }
  /**
   * Returns the metadata of the ROFL file.
   * 
   * @returns {Metadata} The metadata of the ROFL file.
   */
  getMetadata() {
    return this.parser.parse();
  }
};
export {
  Metadata,
  ROFLReader
};
