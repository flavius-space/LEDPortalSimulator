public enum PBColorOrder {
	// RGBW((0 << 6) | (1 << 4) | (2 << 2) | (3 << 0), 4),
	RGBW(0, 1, 2, 3),
	RGB(0, 1, 2)
	;
	public final byte colorOrder;
	public final byte numElements;
	public static final int[] LXColorIdxLookup = new int[]{2, 1, 0, 3};
	private PBColorOrder(int redi, int greeni, int bluei, int whitei, int numElements) {
		this.colorOrder = (byte)(
			((redi & 0b11) << 0)
			| ((greeni & 0b11) << 2)
			| ((bluei & 0b11) << 4)
			| ((whitei & 0b11) << 6));
		this.numElements = (byte) numElements;
	}
	private PBColorOrder(int redi, int greeni, int bluei, int whitei) {
		this(redi, greeni, bluei, whitei, 4);
	}
	private PBColorOrder(int redi, int greeni, int bluei) {
		this(redi, greeni, bluei, 0, 3);
	}

	public byte[] colorBytes(int color) {
		byte[] result = new byte[this.numElements];
		char[] colorNames = new char[]{'r', 'g', 'b', 'w'};
		System.out.print("color: {");
		for(int colorIdx=0; colorIdx<this.numElements; colorIdx++) {
			int index = (this.colorOrder >> (2 * colorIdx)) & 0b11;
			result[index] = LPByteUtils.asByte(color >> (8 * LXColorIdxLookup[colorIdx]) & LPByteUtils.uint8Max);
			System.out.printf("%c: 0x%02x; ", colorNames[colorIdx], result[index]);
		}
		System.out.println("}");
		return result;
	}
}
