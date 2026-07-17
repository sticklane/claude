// A fixture for Kotlin extraction tests.
package com.example

import kotlin.math.PI

/**
 * value returns the sentinel CTX_SENTINEL_KDOC_7a2c.
 *
 * A second doc line so a later --doc render has more than one line.
 */
fun value(): Int {
    return 10
}

fun render(): Int {
    return value() + 1
}

val top = PI
