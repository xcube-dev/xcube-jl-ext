/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2019-2023 by the xcube development team and contributors.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is furnished to do
 * so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * Call asynchronous function `fetchValue` until it returns a value without throwing an exception.
 * If it throws an exception, it will be executed after a delay of `timeout / maxCount`.
 * This is repeated until `maxCount` is reached. Eventually, the last exception will be thrown.
 *
 * @param fetchValue The asynchronous function to be called.
 * @param timeout Overall timeout in milliseconds.
 * @param maxCount Maximum number of failures.
 */
export async function callUntil<T>(fetchValue: () => Promise<T>, timeout: number, maxCount: number): Promise<T> {
    const delay = timeout / maxCount;

    const handler = (resolve: (v: T) => any, count: number) => {
        console.debug(`Fetching ${fetchValue} (attempt ${count}/${maxCount})`)
        fetchValue()
            .then(value => resolve(value))
            .catch(error => {
                if (count <= maxCount) {
                    setTimeout(() => handler(resolve, count + 1), delay);
                } else {
                    throw error;
                }
            });
    };

    return new Promise(resolve => {
        setTimeout(() => handler(resolve, 0), delay);
    });
}


