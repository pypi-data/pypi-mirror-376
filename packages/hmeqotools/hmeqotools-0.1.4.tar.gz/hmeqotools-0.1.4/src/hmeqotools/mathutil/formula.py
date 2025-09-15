from __future__ import annotations

import math
import multiprocessing
import os

from rich.console import Console
from rich.progress import (
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from hmeqotools.mathutil import dec
from hmeqotools.mathutil import funcs as mfn

console = Console()


def _blend_list(lst, unit_size, start_index=0):
    """拌匀列表元素.

    :param lst: 列表
    :param unit_size: 多少元素视作一个单位，按照这个单位排序
    :param start_index: 起始排序位置
    """
    lst_len = len(lst)
    sort_len = lst_len - start_index
    if sort_len > 2:
        sort_len = lst_len - lst_len % unit_size
        mid_index = sort_len // 2
        mid_index = mid_index - mid_index % unit_size + start_index
        sort_len += start_index
        for i, i2 in zip(range(start_index, mid_index, unit_size * 2), range(sort_len, mid_index + 1, -unit_size * 2)):
            lst[i : i + unit_size], lst[i2 - unit_size : i2] = lst[i2 - unit_size : i2], lst[i : i + unit_size]


class Pi:
    k = 10

    @classmethod
    def prec(cls, precision=16) -> int:
        k = cls.k + len(str(precision)) + 1
        pre = precision + k
        b = 10**pre
        x1 = b * 4 // 5
        x2 = b // -239
        s1 = -25
        s2 = -57121
        result = x1 + x2

        n = int(pre * 1.5)
        for i in range(3, n, 2):
            x1 //= s1
            x2 //= s2
            x = (x1 + x2) // i
            if x == 0:
                break
            result += x
        result = result * 4 // 10**k
        return result

    @classmethod
    def ramanujan(cls, n: int, is_prec=True, space_for_time=False) -> int:
        """Ramanujan formulas.

        WARNING: is used multiprocessing,
        please write in `if __name__ == __main__`.
        """
        cpu_count = os.cpu_count()
        assert isinstance(cpu_count, int)
        with multiprocessing.Pool(processes=cpu_count) as pool:
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns()[:-1],
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=False,
            ) as progress:
                task1 = progress.add_task("Ramanujan", total=None)
                task2 = progress.add_task("Ramanujan", total=1, start=False)
                valid_digits = 14
                if is_prec:
                    iter_count = n / valid_digits
                    if iter_count % 1:
                        iter_count += 1
                    iter_count = int(iter_count)
                else:
                    iter_count = n
                prec = valid_digits * iter_count
                progress.update(task1, total=iter_count)

                result = dec.Decimal(0, 0, prec + cls.k)
                count = 4 * cpu_count

                if space_for_time:
                    ftrs = [i for i in mfn.factorial_gen(6 * iter_count)]
                    params = [(i, result, (ftrs[i], ftrs[3 * i], ftrs[6 * i])) for i in range(iter_count)]
                    del ftrs
                    # 对参数排序，使进度条过渡更平滑
                    _blend_list(params, cpu_count)
                    while params:
                        result += sum(pool.map(cls._ramanujan2, params[:count]))
                        progress.update(task1, advance=len(params[:count]))
                        del params[:count]
                else:
                    params = [(i, result) for i in range(iter_count)]
                    _blend_list(params, cpu_count)
                    while params:
                        result += sum(pool.map(cls._ramanujan, params[:count]))
                        progress.update(task1, advance=len(params[:count]))
                        del params[:count]

                progress.start_task(task2)
                result = 426880 * result.convert_int(10005).root(2) / result
                result = result.n // 10 ** (result.dp - (n if is_prec else prec))
                progress.update(task2, completed=1)
        return result

    @staticmethod
    def _ramanujan(k):
        k, dec_ = k
        return dec_.convert_int(math.factorial(6 * k) * (13591409 + 545140134 * k)) / (
            math.factorial(3 * k) * math.factorial(k) ** 3 * (-640320) ** (3 * k)
        )

    @staticmethod
    def _ramanujan2(k):
        k, dec_, ftrs = k
        return dec_.convert_int(ftrs[2] * (13591409 + 545140134 * k)) / (ftrs[1] * ftrs[0] ** 3 * (-640320) ** (3 * k))

    @classmethod
    def machin(cls, precision=16) -> int:
        """马青公式 (内置进度条)."""
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns()[:-1],
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            task1 = progress.add_task("Machin", total=None)
            console.log("初始化变量...")
            # 多计算k位，防止尾数取舍的影响
            k = cls.k + len(str(precision)) + 1
            pre = precision + k
            b = 10**pre
            # 求含4/5的首项
            # 求含1/239的首项
            x1 = b * 4 // 5
            x2 = b // -239
            # x1 = b * 16 // 5
            # x2 = b * 4 // -239
            s1 = -25
            s2 = -57121
            # 求第一大项
            result = x1 + x2

            # 设置下面循环的终点，即共计算n项
            n = int(2 * pre * 0.75)
            progress.update(task1, total=n + 2)
            # 循环初值=3，末值2n,步长=2
            for i in range(3, n, 2):
                # 求每个含1/5的项及符号
                x1 //= s1
                # 求每个含1/239的项及符号
                x2 //= s2
                # 求两项之和
                x = (x1 + x2) // i
                if x == 0:
                    break
                # 求总和
                result += x
                progress.update(task1, advance=2)
            # 求出π 并 舍掉后k位
            # result //= 10 ** k
            result = result * 4 // 10**k
            progress.update(task1, completed=n + 2)
        return result


class E:
    k = 10

    @classmethod
    def taylor(cls, precision=16) -> int:
        """Taylor formulas.

        !!! warning
            warning: is used multiprocessing
        """
        # 计算时的精度
        p1 = precision + len(str(precision)) + cls.k
        # 迭代次数，精度越高，此数值越小
        if p1 < 100:
            # p1 < 100
            p2 = p1
        elif p1 < 500:
            # 100 <= p1 < 500
            p2 = 65 * p1 // 100
        elif p1 < 1000:
            # 500 <= p1 < 1000
            p2 = 50 * p1 // 100
        elif p1 < 5000:
            # 1000 <= p1 < 5000
            p2 = 45 * p1 // 100
        elif p1 < 10000:
            # 5000 <= p1 < 10000
            p2 = 36 * p1 // 100
        elif p1 < 100000:
            # 10000 <= p1 < 100000
            p2 = 33 * p1 // 100
        else:
            # 100000 <= p1
            p2 = 30 * p1 // 100

        cpu_count = os.cpu_count()
        assert isinstance(cpu_count, int)
        with multiprocessing.Pool(processes=cpu_count) as pool:
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns()[:-1],
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=False,
            ) as progress:
                task1 = progress.add_task("Taylor", total=None)
                result = dec.Decimal(0, 0, p1)
                one = result.convert_int(1)
                count = 64 * cpu_count

                params = [(one, i) for i in mfn.factorial_gen(p2)]
                _blend_list(params, count)
                progress.update(task1, total=len(params))
                while params:
                    result += sum(pool.map(cls._taylor, params[:count]))
                    progress.update(task1, advance=len(params[:count]))
                    del params[:count]
        return result.n // 10 ** (result.dp - precision)

    @staticmethod
    def _taylor(k):
        return k[0] / k[1]


def main():
    E.taylor(50000)


if __name__ == "__main__":
    main()
