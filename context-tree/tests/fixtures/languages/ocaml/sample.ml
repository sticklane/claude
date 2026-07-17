open Printf

(** value returns the sentinel CTX_SENTINEL_OCAMLDOC_3b9d.

    A second doc line so a later --doc render has more than one line. *)
let value = 10

let render x =
  let y = value in
  y + x

module Inner = struct
  let nested = 1
end
