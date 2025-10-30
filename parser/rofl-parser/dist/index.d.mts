interface IRawMetadata {
    readonly gameLength: number;
    readonly lastGameChunkId: number;
    readonly lastKeyFrameId: number;
    readonly statsJson: string;
}
interface IJSONStat {
    [key: string]: string;
}
interface IProcessedMetadata {
    readonly gameLength: number;
    readonly lastGameChunkId: number;
    readonly lastKeyFrameId: number;
    readonly statsJson: Array<IJSONStat>;
}
type RawMetadata = IRawMetadata;
type ProcessedMetadata = IProcessedMetadata;
type JSONStats = Array<IJSONStat>;

declare class Metadata implements ProcessedMetadata {
    readonly gameLength: number;
    readonly lastGameChunkId: number;
    readonly lastKeyFrameId: number;
    readonly statsJson: JSONStats;
    constructor(metadata: RawMetadata);
    toString(): string;
    toBuffer(): Buffer;
}

/**
 * `ROFLReader` is a class that reads and parses a ROFL file.
 * It determines the appropriate parser to use based on the file version.
 *
 * @property {Buffer} file - The ROFL file to be parsed.
 * @property {Parser} parser - The parser to be used.
 */
declare class ROFLReader {
    private file;
    private parser;
    /**
     * Creates a new instance of the ROFLReader.
     *
     * @param {string | Buffer} pathOrBuffer - The path to the ROFL file or the file as a Buffer.
     * @throws {Error} If the file does not exist or is not a valid ROFL file.
     */
    constructor(pathOrBuffer: string | Buffer);
    /**
     * Determines the appropriate parser to use based on the file version.
     *
     * @returns {Parser} The appropriate parser.
     */
    private determineParser;
    /**
     * Returns the metadata of the ROFL file.
     *
     * @returns {Metadata} The metadata of the ROFL file.
     */
    getMetadata(): Metadata;
}

export { type JSONStats, Metadata, type ProcessedMetadata, ROFLReader, type RawMetadata };
