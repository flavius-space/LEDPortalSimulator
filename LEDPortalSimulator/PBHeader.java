public class PBHeader {
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
		for(char c : magic.toCharArray()) {
			message[i++] = (byte) c;
		}
		message[i++] = (byte) this.channel;
		message[i++] = (byte) this.recordType.value;

		return message;
	}
}
