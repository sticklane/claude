package antigravity

import "testing"

// --- test helpers: hand-build protobuf wire bytes (no protoc, no .db file) ---

// uvarint encodes v as a base-128 varint.
func uvarint(v uint64) []byte {
	var out []byte
	for v >= 0x80 {
		out = append(out, byte(v)|0x80)
		v >>= 7
	}
	return append(out, byte(v))
}

// tag encodes a (field number, wire type) tag.
func tag(num, wireType int) []byte {
	return uvarint(uint64(num)<<3 | uint64(wireType))
}

// varintField encodes a wire-type-0 field.
func varintField(num int, v uint64) []byte {
	return append(tag(num, 0), uvarint(v)...)
}

// lenField encodes a wire-type-2 (length-delimited) field.
func lenField(num int, payload []byte) []byte {
	b := tag(num, 2)
	b = append(b, uvarint(uint64(len(payload)))...)
	return append(b, payload...)
}

// strField encodes a wire-type-2 field carrying a UTF-8 string.
func strField(num int, s string) []byte {
	return lenField(num, []byte(s))
}

func TestProtowireVarintDecode(t *testing.T) {
	cases := []struct {
		name string
		want uint64
	}{
		{"zero", 0},
		{"one-byte-max", 127},
		{"two-byte-min", 128},
		{"three-hundred", 300},
		{"large", 1 << 40},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			enc := uvarint(c.want)
			got, n, ok := Varint(enc)
			if !ok {
				t.Fatalf("Varint(%v) not ok", enc)
			}
			if got != c.want {
				t.Errorf("Varint value = %d, want %d", got, c.want)
			}
			if n != len(enc) {
				t.Errorf("Varint consumed %d bytes, want %d", n, len(enc))
			}
		})
	}
}

func TestProtowireReadsSingleVarintField(t *testing.T) {
	data := varintField(1, 42)
	f, ok := ReadField(data, 1)
	if !ok {
		t.Fatalf("ReadField(1) not found")
	}
	if f.WireType != 0 {
		t.Errorf("WireType = %d, want 0", f.WireType)
	}
	if f.Varint != 42 {
		t.Errorf("Varint = %d, want 42", f.Varint)
	}
}

func TestProtowireReadsLengthDelimitedField(t *testing.T) {
	// mirrors gen_metadata field 19 (short model slug)
	data := strField(19, "gemini-default")
	f, ok := ReadField(data, 19)
	if !ok {
		t.Fatalf("ReadField(19) not found")
	}
	if f.WireType != 2 {
		t.Errorf("WireType = %d, want 2", f.WireType)
	}
	if string(f.Bytes) != "gemini-default" {
		t.Errorf("Bytes = %q, want %q", string(f.Bytes), "gemini-default")
	}
}

func TestProtowireNestedFieldPath(t *testing.T) {
	// Mirror the spec's nested-submessage descent (the 9.4 Timestamp shape):
	// outer field 4 = submessage, whose field 9 = submessage, whose field 4 =
	// a Timestamp submessage carrying seconds (field 1) as a varint.
	timestamp := varintField(1, 1_700_000_000) // seconds
	inner9 := lenField(4, timestamp)           // field 4 inside the field-9 submessage
	outer4 := lenField(9, inner9)              // field 9 inside the field-4 submessage
	data := lenField(4, outer4)                // outer field 4

	f, ok := ReadPath(data, 4, 9, 4, 1)
	if !ok {
		t.Fatalf("ReadPath(4,9,4,1) not found")
	}
	if f.WireType != 0 {
		t.Errorf("WireType = %d, want 0 (varint seconds)", f.WireType)
	}
	if f.Varint != 1_700_000_000 {
		t.Errorf("seconds = %d, want 1700000000", f.Varint)
	}
}

func TestProtowireRepeatedMapField(t *testing.T) {
	// mirrors gen_metadata field 20: repeated {1: key, 2: value} string map.
	entry := func(k, v string) []byte {
		body := append(strField(1, k), strField(2, v)...)
		return lenField(20, body)
	}
	var data []byte
	data = append(data, entry("model_enum", "MODEL_PLACEHOLDER_M20")...)
	data = append(data, entry("trajectory_id", "traj-abc")...)
	data = append(data, entry("used_claude", "false")...)

	fields, ok := Walk(data)
	if !ok {
		t.Fatalf("Walk failed on repeated map")
	}
	got := map[string]string{}
	for _, f := range fields {
		if f.Num != 20 {
			continue
		}
		k, kok := ReadField(f.Bytes, 1)
		v, vok := ReadField(f.Bytes, 2)
		if !kok || !vok {
			t.Fatalf("map entry missing key or value")
		}
		got[string(k.Bytes)] = string(v.Bytes)
	}
	want := map[string]string{
		"model_enum":    "MODEL_PLACEHOLDER_M20",
		"trajectory_id": "traj-abc",
		"used_claude":   "false",
	}
	if len(got) != len(want) {
		t.Fatalf("got %d pairs, want %d: %v", len(got), len(want), got)
	}
	for k, v := range want {
		if got[k] != v {
			t.Errorf("pair %q = %q, want %q", k, got[k], v)
		}
	}
}

func TestProtowireMalformedTruncatedVarintDoesNotPanic(t *testing.T) {
	// A varint whose continuation bit never clears must not loop forever.
	data := append(tag(1, 0), 0xFF, 0xFF, 0xFF) // field 1 varint, never terminates
	fields, ok := Walk(data)
	if ok {
		t.Errorf("Walk on truncated varint returned ok=true, want false (fields=%v)", fields)
	}
}

func TestProtowireLengthExceedsRemainingSkips(t *testing.T) {
	// A length-delimited field declaring more bytes than remain must fail, not panic.
	data := tag(5, 2)
	data = append(data, uvarint(100)...) // claims 100 bytes
	data = append(data, 0x01, 0x02)      // only 2 present
	if _, ok := Walk(data); ok {
		t.Errorf("Walk on over-long length returned ok=true, want false")
	}
}

func TestProtowireUnknownFieldSkipped(t *testing.T) {
	// An unknown field (varint) followed by a known length-delimited field:
	// the known field must still be extractable.
	var data []byte
	data = append(data, varintField(5, 999)...)       // unknown numeric field
	data = append(data, lenField(7, []byte{0, 1})...) // unknown opaque blob
	data = append(data, strField(19, "gemini-default")...)

	f, ok := ReadField(data, 19)
	if !ok {
		t.Fatalf("ReadField(19) not found after unknown fields")
	}
	if string(f.Bytes) != "gemini-default" {
		t.Errorf("Bytes = %q, want %q", string(f.Bytes), "gemini-default")
	}

	// And the whole message still walks cleanly.
	fields, ok := Walk(data)
	if !ok {
		t.Fatalf("Walk failed with unknown fields present")
	}
	if len(fields) != 3 {
		t.Errorf("walked %d fields, want 3", len(fields))
	}
}
