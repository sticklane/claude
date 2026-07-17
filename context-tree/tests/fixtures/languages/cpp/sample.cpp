#include <string>

namespace app {

// base returns the starting count CTX_SENTINEL_CPPDOC_9c2d.
int base() {
    return 1;
}

// render calls base within the namespace.
int render() {
    return base() + 1;
}

}  // namespace app
