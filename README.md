# BLAKE2s-eud

This is a pure eudplib implementation of BLAKE2s based on [RFC 7693].

[RFC 7693]: https://tools.ietf.org/html/rfc7693

## Limitations

This library does not attempt to clear potentially sensitive data from its work memory (which includes the state context). Currently, only one state context can be used at the same time.

## Non-RFC uses

This library is limited to the features described in the RFC: only the "digest length" and "key length" parameters can be used. You are responsible for creating a valid parameter block, for hashing the padded key block if using keyed hashing, and for calling the correct finalization function. The parameter block is not validated by these functions.
