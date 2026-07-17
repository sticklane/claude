import { helper } from "./helper";

/**
 * Return the sentinel CTX_SENTINEL_TSDOC_9b2c marker.
 *
 * A second doc line so a later `ctx sig --doc` has more than one line.
 */
export function value(): number {
  return GLOBAL_VALUE;
}

const GLOBAL_VALUE = 10;

export namespace Outer {
  export class Inner {
    deep(): number {
      // Cross-symbol call to the module-level `value` function.
      return value() + helper();
    }
  }
}

export class Widget {
  render(): number {
    // `value` here is a function-local that shadows the module-level
    // `value` function of the same name.
    const value = 42;
    return value;
  }
}
