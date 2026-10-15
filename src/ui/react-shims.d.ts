/** 首轮静态部署使用 UMD React；迁移到模块化 React 后删除此过渡声明。 */
declare namespace React {
  function createElement(type: unknown, props: Record<string, unknown> | null, ...children: unknown[]): unknown;
  class Component<P = object, S = object> {
    constructor(props: P);
    readonly props: Readonly<P>;
    state: Readonly<S>;
    setState(state: Partial<S>): void;
    render(): unknown;
  }
}
declare const ReactDOM: { render(element: unknown, container: Element): void };
declare namespace JSX {
  interface IntrinsicElements { [elementName: string]: Record<string, unknown> }
}
