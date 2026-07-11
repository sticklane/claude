// Package antigravity parses Antigravity CLI session logs
// (~/.gemini/antigravity-cli/conversations/*.db) into agentprof samples.
//
// protowire.go is a TARGETED protobuf wire-format field-walker, NOT a
// general protobuf decoder. Antigravity ships no .proto schema, so this
// reader extracts only the specific (field number, wire type) paths this
// adapter needs — e.g. gen_metadata field 4 (token counts), 9.4 (Timestamp),
// 19/21 (model strings), and the repeated {key,value} map at field 20; and
// trajectory_metadata_blob's field 1/6/18 — treating every other field as
// opaque and skippable, which is exactly the wire format's self-describing
// design (each field carries its own tag and length). The exact field paths
// it must support are enumerated in SPEC.md, Solution item 1.
//
// Malformed or unrecognized bytes cause a per-call ok=false return, never a
// panic and never an infinite loop, matching SCHEMA.md's skip-on-bad-input
// philosophy. There is deliberately no field-name registry or codegen here.
package antigravity

// maxVarintBytes bounds a base-128 varint to the 10 bytes a 64-bit value can
// occupy, so a stream of continuation bytes can never loop unbounded.
const maxVarintBytes = 10

// Field is one decoded protobuf field.
//
// For wire type 0 (varint) and 1/5 (fixed64/fixed32), Varint holds the
// numeric value (fixed widths are read little-endian) and Bytes holds the
// raw payload. For wire type 2 (length-delimited: strings, bytes, embedded
// submessages), Bytes holds the payload and Varint is unused.
type Field struct {
	Num      int
	WireType int
	Varint   uint64
	Bytes    []byte
}

// Varint decodes a base-128 varint from the front of data, returning the
// value, the number of bytes consumed, and ok=false if the input is
// truncated or the varint exceeds 10 bytes (never terminates).
func Varint(data []byte) (val uint64, n int, ok bool) {
	var shift uint
	for i := 0; i < len(data); i++ {
		if i >= maxVarintBytes {
			return 0, 0, false
		}
		b := data[i]
		val |= uint64(b&0x7f) << shift
		if b < 0x80 {
			return val, i + 1, true
		}
		shift += 7
	}
	return 0, 0, false // ran out of bytes before the continuation bit cleared
}

// Walk parses every top-level field in data. It returns ok=false on any
// malformed input (truncated tag/varint, an unsupported wire type such as
// the deprecated groups 3/4, or a length-delimited field whose declared
// length exceeds the remaining bytes) rather than partial results a caller
// might mistake for a complete parse.
func Walk(data []byte) (fields []Field, ok bool) {
	pos := 0
	for pos < len(data) {
		tag, n, tok := Varint(data[pos:])
		if !tok {
			return nil, false
		}
		pos += n

		f := Field{Num: int(tag >> 3), WireType: int(tag & 0x7)}
		switch f.WireType {
		case 0: // varint
			v, vn, vok := Varint(data[pos:])
			if !vok {
				return nil, false
			}
			f.Varint = v
			pos += vn
		case 1: // 64-bit fixed
			if pos+8 > len(data) {
				return nil, false
			}
			f.Bytes = data[pos : pos+8]
			f.Varint = leUint(f.Bytes)
			pos += 8
		case 2: // length-delimited
			length, ln, lok := Varint(data[pos:])
			if !lok {
				return nil, false
			}
			pos += ln
			end := pos + int(length)
			if int(length) < 0 || end < pos || end > len(data) {
				return nil, false // declared length overruns the buffer
			}
			f.Bytes = data[pos:end]
			pos = end
		case 5: // 32-bit fixed
			if pos+4 > len(data) {
				return nil, false
			}
			f.Bytes = data[pos : pos+4]
			f.Varint = leUint(f.Bytes)
			pos += 4
		default: // groups (3/4) and any other wire type: unsupported
			return nil, false
		}
		fields = append(fields, f)
	}
	return fields, true
}

// ReadField returns the FIRST field with the given number in data. It returns
// ok=false if data is malformed or no such field exists. For repeated fields
// (e.g. the field-20 string map), use Walk and filter by Num to see every
// occurrence.
func ReadField(data []byte, num int) (Field, bool) {
	fields, ok := Walk(data)
	if !ok {
		return Field{}, false
	}
	for _, f := range fields {
		if f.Num == num {
			return f, true
		}
	}
	return Field{}, false
}

// ReadPath descends nested length-delimited submessages following path: each
// element selects the first field with that number at the current level, then
// descends into its Bytes for the next element. The final element is returned
// as-is (it may be any wire type, e.g. the varint seconds inside a Timestamp).
// Returns ok=false if any element is missing, if an intermediate field is not
// length-delimited, or if any level is malformed.
func ReadPath(data []byte, path ...int) (Field, bool) {
	if len(path) == 0 {
		return Field{}, false
	}
	cur := data
	for i, num := range path {
		f, ok := ReadField(cur, num)
		if !ok {
			return Field{}, false
		}
		if i == len(path)-1 {
			return f, true
		}
		if f.WireType != 2 {
			return Field{}, false // can only descend into a submessage
		}
		cur = f.Bytes
	}
	return Field{}, false
}

// leUint reads up to 8 bytes little-endian into a uint64.
func leUint(b []byte) uint64 {
	var v uint64
	for i := 0; i < len(b) && i < 8; i++ {
		v |= uint64(b[i]) << (8 * uint(i))
	}
	return v
}
