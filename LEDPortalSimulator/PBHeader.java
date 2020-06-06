public class PBHeader {
	public static final boolean debug = false;
	public static final int size = 6;
	public static final String magic = "UPXL";
	public int channel;
	public PBRecordType recordType;
	public PBHeader(final int channel, final PBRecordType recordType) {
		this.channel = channel;
		this.recordType = recordType;
	}
	public byte[] toBytes() {
		final byte[] message = new byte[size];
		int i=0;
		if (debug) System.out.printf("magic: %s\n", magic);
		for(char c : magic.toCharArray()) {
			message[i++] = (byte) c;
		}
		if (debug) System.out.printf("channel: %d\n", this.channel);
		message[i++] = (byte) this.channel;
		if (debug) System.out.printf("recordtype: %d (%s)\n", this.recordType.value, this.recordType.name());
		message[i++] = (byte) this.recordType.value;

		return message;
	}
}