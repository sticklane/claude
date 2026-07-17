// A fixture for Java extraction tests.
package com.example;

import java.util.List;
import java.util.ArrayList;

/** Sample is the fixture container class. */
public class Sample {
    private int global = 10;

    /**
     * Return the sentinel CTX_SENTINEL_JAVADOC_8f1b marker.
     *
     * A second doc line so a later --doc render has more than one line.
     */
    public int value() {
        return global;
    }

    public int render() {
        List<Integer> items = new ArrayList<>();
        return value() + items.size();
    }
}
