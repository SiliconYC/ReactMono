export function routeSteps(route, from, steps) {
    if (route.length === 0 || new Set(route).size !== route.length) {
        throw new Error('演示路线必须包含不重复的格子');
    }
    if (!Number.isSafeInteger(steps) || steps < 0) {
        throw new Error('演示移动步数非法');
    }
    const startIndex = route.indexOf(from);
    if (startIndex < 0)
        throw new Error('演示路线不存在角色当前位置');
    return Array.from({ length: steps }, (_, offset) => route[(startIndex + offset + 1) % route.length]);
}
