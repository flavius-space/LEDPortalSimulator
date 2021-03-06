import java.util.logging.Logger;

public abstract class PBMessageFactory {
	private static final Logger logger = Logger.getLogger(PBMessageFactory.class.getName());
	public static final int crcSize = LPByteUtils.uint32Bytes;
	public final PBRecordType recordType;
	public final int channel;
	public PBCRC crc;
	/**
	 * Number of bytes between header and CRC when there are zero colors being sent.
	 */
	public final int baseSize;
	/**
	 * Number of bytes occupied by each color
	 */
	public final int colorSize;
	public PBMessageFactory(PBRecordType recordType, int channel, int baseSize, int colorSize) {
		this.recordType = recordType;
		this.channel = channel;
		this.baseSize = baseSize;
		this.colorSize = colorSize;
		this.crc = new PBCRC();
	}

	public PBMessageFactory(PBRecordType recordType) {
		this(recordType, 0, 0, 0);
	}

	/**
	 * writeHeader
	 * Write the header to the message buffer at offset
	 */
	public int writeHeader(byte[] message, int offset) {
		int i=offset;
		for(byte b : new PBHeader(this.channel, this.recordType).toBytes()) {
			message[i++] = b;
		};
		return (i - offset);
	}

	public int getBodySize(int[] colorIndices) {
		return baseSize + (colorIndices.length * colorSize);
	}

	protected int writeBody(byte[] message, int offset, int[] colorIndices, int[] colors) {
		return 0;
	}

	protected int writeCRC(byte[] message, int offset) {
		int i=offset;
		for(byte b : this.crc.toBytes()) message[i++] = b;
		return (i - offset);
	}

	public int getMessageSize(int[] colors) {
		return PBHeader.size + this.getBodySize(colors) + crcSize;
	}
	/**
	 * Get the header and body of the message
	*/
	public byte[] getMessage(int[] colorIndices, int[] colors) {
		this.crc.reset();
		final byte[] message = new byte[this.getMessageSize(colorIndices)];
		int i=0;
		i += this.writeHeader(message, i);
		i += this.writeBody(message, i, colorIndices, colors);
		this.crc.updateBytes(message, 0, i);
		i += this.writeCRC(message, i);
		return message;
	}

	public byte[] getMessage() {
		return getMessage(new int[]{}, new int[]{});
	}
}
