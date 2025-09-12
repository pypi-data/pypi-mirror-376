# Примеры новых вариантов использования кода

## Предкомпенсация классическими (не нейросетевыми методами)

### Предкомпенсация рефракционных искажений (РИЗ)

Рассмотрим примеры предкомпенсации рефракционных искажений классическими (не-нейросетевыми методами) при помощи нашего фреймворка

#### Метод Хуанга

Метод Huang — численный алгоритм предкомпенсации, основанный на **фильтре Винера**,  используемый для восстановления изображений, искажённых аберрациями зрения (PSF).  Он не требует обучения и применяется как базовый метод для оценки эффективности нейросетевых подходов.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение, нормализованное в диапазоне [0, 1].

📖 Подробнее: Jian Huang,  
*Dynamic Image Precompensation for Improving Visual Performance of Computer Users with Ocular Aberrations*,  
Master's Thesis, Florida International University, 18 июня 2013.  
[Скачать PDF](https://digitalcommons.fiu.edu/cgi/viewcontent.cgi?article=2021&context=etd)
 
Используйте следующий код:

    from __future__ import annotations

    from typing import Callable
    from torch import Tensor

    from olimp.processing import scale_value
    from olimp.precompensation._demo import demo
    from olimp.precompensation.basic.huang import huang

    if __name__ == "__main__":

        def demo_huang(
            image: Tensor,
            psf: Tensor,
            progress: Callable[[float], None],
        ) -> Tensor:
            ret = huang(image, psf)
            progress(1.0)
            return scale_value(ret, min_val=0, max_val=1.0)

        demo("Huang", demo_huang, mono=False)

Здесь:

- `torch.Tensor` — работа с тензорами в PyTorch;
- `Callable` — тип аннотации из `typing`;
- `scale_value`, `fft_conv` — функции обработки изображений из модуля `olimp.processing` в составе нашего фреймворка;
- `demo`, `demo_cvd` — утилиты для демонстрации предкомпенсации изображений.

Этот код для удобства внесен в файл olimp/examples/precompensation/huang.py и может быть запущен командой 

    python3 -m olimp.examples.precompensation.huang

В результате запуска этот вызов выдаст окно с 4 изображениями: визуализацией функции рассеяния точки (ФРТ, PSF), исходным изображением, результатом предкомпенсации и симуляцией, как предкомпенсированное изображением будет видно неидеальной зрительной системой с данной ФРТ. 

### Метод Feng Xu

Метод Feng Xu — численный алгоритм предкомпенсации, разработанный для вычислений в **реальном времени**  
и оптимизированный для **GPU-вычислений**. Основан на **L2-деконволюции** в частотной области (FFT)  
с параметром регуляризации `λ`, позволяющим контролировать диапазон значений пикселей.

**Вход:**
- изображение;
- PSF (функция рассеяния точки);
- параметр регуляризации `lambda_val` (например, λ = 2).

**Выход:**
- предкомпенсированное изображение (может быть нормализовано или дополнительно обработано).

📖 Подробнее: Feng Xu,  
*Software Based Visual Aberration Correction for HMDs*, IEEE VR, март 2018.  
[Скачать PDF](https://www.cs.ucf.edu/courses/cap6121/spr2024/readings/Xu2018.pdf)

Для вызова используйте код из файла olimp/examples/precompensation/feng_xu.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation.feng_xu


### Метод Bregman Jumbo

Метод Bregman Jumbo — численный алгоритм оптимизации, основанный на **вариационной формулировке задачи предкомпенсации**, в которой используется регуляризация с **обратной проекцией Брегмана** и решается задача минимизации с ограничениями.  
Алгоритм впервые был предложен в 2021 году, а в 2024 году был доработан авторами данной работы для повышения качества и устойчивости.

**Особенности:**
- Использует метод Брегмана для поиска решения задачи с ограничением по диапазону пикселей;
- В оригинале — решение через итеративную схему с TV-регуляризацией;
- В доработке (2024) — улучшена сходимость, добавлена адаптация параметров и альтернативная схема обновления переменных.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение.

📖 Подробнее:  
**Оригинальный метод** — Montalto et al., *JUMBO: Joint Unrolling Optimization and Model-Based Approach for Blind Image Deconvolution*, ICCV 2021.  
[Скачать PDF](https://drive.google.com/file/d/1TQs41VJY4Bw05bAOMTacS6zZx0d9tK01/view?usp=sharing)  
**Доработка** — Abgaryan A.A., Al-Kazir N.B., *Анализ и улучшение оптимизации Брегмана в задачах предкомпенсации: новые подходы и алгоритмические решения*, 2024.  
[Скачать PDF (на русском)](attachment:/mnt/data/2024_AbgaryanAA_Al_KazirNB_Analiz_i_uluchshenie_optimizatsii_Bregmana_v_zadachakh_predkompensatsii_novye_podkhody_i_algoritmicheskie_k_id3179_v2024_1219_1739_.pdf)

Для вызова используйте код из файла olimp/examples/precompensation/bregman_jumbo.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation.bregman_jumbo

### Метод Global Tone Mapping (GTM)

Метод Global Tone Mapping — численный метод глобального тонального отображения,  
разработанный для предкомпенсации изображений с учётом **рефракционных искажений зрения**.  
Он оптимизирует глобальную кривую отображения с помощью градиентного спуска,  
обеспечивая более естественную и корректную передачу яркости и контраста после прохождения через искажающую PSF.

**Ключевые особенности:**
- Не требует обучения модели;
- Параметризованная глобальная кривая яркости оптимизируется по заданной функции потерь;
- Применяется в задачах предкомпенсации зрения с искажениями, вызванными аберрациями.

**Вход:**
- изображение;
- PSF (функция рассеяния точки);
- параметры оптимизации (`lr`, число итераций и др.).

**Выход:**
- предкомпенсированное изображение после применения глобальной тональной кривой.

📖 Подробнее:  
Al-Kazir N.B., Nikolaev I.P., Nikolaev D.P.,  
*Search for Image Quality Metrics Suitable for Assessing Images Specially Precompensated for Users with Refractive Vision Defects*,  
HSE, 2023.  
[Скачать PDF](https://publications.hse.ru/pubs/share/direct/932038377.pdf)

Для вызова используйте код из файла olimp/examples/precompensation/global_tone_mapping.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation.global_tone_mapping


### Метод HQS (Half-Quadratic Splitting)

Метод HQS — численный итеративный алгоритм, основанный на **методе полу квадратичного разделения**,  
используется для предкомпенсации изображений, искажённых аберрациями зрения (PSF).  
Метод формулируется как задача оптимизации с двумя подзадачами:  
градиентная регуляризация и согласование с искажённым изображением.  
Он не требует обучения и решается с помощью градиентного спуска.

**Ключевые особенности:**
- Использует градиентную регуляризацию;
- Является расширением вариационных методов;
- Разделение переменных (параметров `p` и `w`) ускоряет сходимость.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение, нормализованное в диапазоне [0, 1].

📌 Публикация отсутствует (метод реализован авторами фреймворка как численный прототип).

Для вызова используйте код из файла olimp/examples/precompensation/hqs.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

     python3 -m olimp.examples.precompensation.hqs



### Метод Ji

Метод Ji — численный алгоритм предкомпенсации, основанный на **кусочно-линейных оценках (Piecewise Linear Estimators, PLE)**  
и использующий разреженное представление градиентов изображения.  
В нашей реализации дополнительно применяется функция потерь **MS-SSIM** для более точной оптимизации в задачах восстановления.

Метод позволяет эффективно восстанавливать изображения, искажённые аберрациями зрения (PSF),  
улучшая визуальное качество по сравнению с классическими методами регуляризации.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение, нормализованное в диапазоне [0, 1].

📖 Подробнее: Hao Ji, Chao Liu, Zuowei Shen, Yinqiang Xu,  
*Efficient Image Deconvolution with Piecewise Linear Estimators*,  
CVPR 2014. [DOI: 10.1109/CVPR.2014.428](https://doi.org/10.1109/CVPR.2014.428)  
[Скачать PDF](sandbox:/mnt/data/10.1109@CVPR.2014.428.pdf)


Для вызова используйте код из файла olimp/examples/precompensation/ji.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

     python3 -m olimp.examples.precompensation.ji


### Метод Montalto (FISTA)

Метод **Montalto (FISTA)** — численный алгоритм предкомпенсации, основанный на  
ускоренной итеративной схеме **FISTA** с регуляризацией **total variation (TV)**.  
Используется для восстановления изображений, искажённых аберрациями зрения (PSF),  
обеспечивая баланс между чёткостью и устойчивостью к шуму.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение с подавленным размытием и улучшенными границами.

📖 Подробнее: Montalto et al.,  
*A Total Variation Approach for Customizing Imagery to Improve Visual Acuity*, 
ACM transactions on graphics (TOG), 2015.  
[Скачать PDF](sandbox:/mnt/data/10.1145@2717307.pdf)

Для вызова используйте код из файла olimp/examples/precompensation/montalto_fista.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

     python3 -m olimp.examples.precompensation.montalto_fista


### Метод Montalto (Adam AMSGrad)

Метод **Montalto (Adam AMSGrad)** — модификация оригинального алгоритма Montalto,  
в которой вместо метода FISTA используется оптимизатор **Adam** с флагом **AMSGrad**  
для повышения устойчивости и сходимости. Метод опирается на **регуляризацию total variation (TV)**  
и предназначен для предкомпенсации искажений, вызванных аберрациями зрения (PSF),  
улучшая резкость и субъективную чёткость изображений.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение, нормализованное в диапазоне [0, 1].

📖 Подробнее:  
Montalto C. et al.  
*A Total Variation Approach for Customizing Imagery to Improve Visual Acuity*,  
ACM transactions on graphics (TOG), 2015.  
[Скачать PDF](sandbox:/mnt/data/10.1145@2717307.pdf)


Для вызова используйте код из файла olimp/examples/precompensation/montalto.py

По структуре код аналогичен используемому в методе Хуанга (см. выше). Для его быстрого запуска используйте команду:

     python3 -m olimp.examples.precompensation.montalto

### Предкомпенсация дефектов цветового зрения (ДЦЗ)

#### Метод Achromatic Daltonization

Метод **Achromatic Daltonization** — это **оптимизационный алгоритм предкомпенсации**,
разработанный специально для коррекции изображений при цветовой слепоте.  
В отличие от классических методов, он формулируется как задача минимизации функционала,  
включающего структурное сходство и яркостное соответствие, и решается численно с помощью градиентного спуска.

Метод позволяет учитывать индивидуальные особенности нарушений цветового восприятия  
(протанопия, дейтеранопия и др.) и адаптировать результат под конкретный тип цветовой слепоты.

#### Вход:
- изображение;
- тип дихроматопсии (например, `protan`);
- функция искажения цвета (`ColorBlindnessDistortion`);
- параметры метода (`ADParameters`, включая функцию потерь и шаги оптимизации).

#### Выход:
- предкомпенсированное изображение (одноканальное или RGB в зависимости от настроек).

📖 Подробнее:  
- Alshammari, F., Tovée, M. J., & Westland, S.,  
**Achromatic Daltonization: A Novel Technique to Enhance Visual Information for Dichromats**,  
*Journal of Imaging*, 2023.  
[Скачать PDF](https://www.mdpi.com/2313-433X/11/7/225)

Для запуска метода используйте следующий код:

    from __future__ import annotations

    from typing import Callable
    from torch import Tensor

    from olimp.precompensation._demo_cvd import demo as demo_cvd
    from olimp.precompensation.optimization.achromatic_daltonization import (
        achromatic_daltonization,
        ColorBlindnessDistortion,
        ADParameters,
        M1Loss,
    )
    import warnings


    def demo_achromatic_daltonization(
        image: Tensor,
        distortion: ColorBlindnessDistortion,
        progress: Callable[[float], None],
    ) -> tuple[Tensor]:

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return (
                achromatic_daltonization(
                    image,
                    distortion,
                    ADParameters(progress=progress, loss_func=M1Loss()),
                ),
            )

    if __name__ == "__main__":

        distortion = ColorBlindnessDistortion.from_type("protan")
        demo_cvd(
            "Achromatic Daltonization",
            demo_achromatic_daltonization,
            distortion=distortion,
        )

Здесь:

- `torch.Tensor` — работа с тензорами в PyTorch;
- `Callable` — тип аннотации из `typing`;
- `M1Loss` — функция потерь;
- `ColorBlindnessDistortion` — симуляция дихроматического искажения; 
- `ADParameters` — класс параметров алгоритма;
- `demo`, `demo_cvd` — утилиты для демонстрации предкомпенсации изображений.

Этот код для удобства внесен в файл olimp/examples/precompensation/achromatic_daltonization.py и может быть запущен командой 

    python3 -m olimp.examples.precompensation.achromatic_daltonization

В результате этого запуска выдается окно с 4 изображениями: исходным, симуляцией его восприятия человеком с ДЦЗ, предкомпенсированным и симуляцией его восприятия.


### Метод CVD Direct Optimization

Метод CVD Direct Optimization — численная оптимизация, направленная на **персонализированную предкомпенсацию**  
дефектов цветового зрения (ДЦЗ), например протанопия, дейтеранопия. Подходит для задач, где необходимо учесть индивидуальные искажения  
зрения наблюдателя (модель `ColorBlindnessDistortion`) и корректировать изображение напрямую без обучения нейросети.

**Ключевые особенности:**
- Использует градиентный спуск с оптимизацией по карте весов (weight map);
- Потери считаются между исходным и симулированным ретинальным изображением;
- Поддерживает любые дифференцируемые функции потерь (например, RMS в Lab-пространстве);
- Реализована ранняя остановка при сходимости по шагу изменения loss.

**Вход:**
- изображение;
- модель искажения зрения (`ColorBlindnessDistortion`);
- параметры оптимизации (скорость обучения, функция потерь и т.п.).

**Выход:**
- предкомпенсированное изображение, предназначенное для наблюдателя с ДЦЗ.

🧪 Метод пока не имеет опубликованных статей, но входит в экспериментальный стек open-source фреймворка `pyolimp`.


Для вызова используйте код из файла olimp/examples/precompensation/cvd_direct_optimization.py

По структуре код аналогичен используемому в методе Achromatic Daltonization (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation.cvd_direct_optimization


### Метод Tennenholtz-Zachevsky

Метод **Tennenholtz-Zachevsky** предназначен для предкомпенсации изображений  
при аномалиях цветового зрения (дихроматии), таких как протанопия и дейтеранопия.  
Метод оптимизирует искажения в LMS-пространстве, минимизируя разницу между  
восприятием исходного и компенсированного изображения для наблюдателя с нарушением.

В качестве функции потерь используется разность в LMS-компонентах,  
а оптимизация проводится в пространстве изображений с применением ограничений  
на допустимые значения яркости.

**Вход:**
- изображение;
- тип цветовой аномалии (например, protan, deutan).

**Выход:**
- предкомпенсированное изображение, адаптированное под тип ДЦЗ.

📖 Подробнее:  
Tennenholtz G., Zachevsky A.  
*A Perception-Based Approach for Color Correction of Dichromats*,  
APSIPA ASC, 2019.  
[Скачать PDF](sandbox:/mnt/data/5c6023e6-9374-4916-b84e-ca7c43b58489.pdf)


Для вызова используйте код из файла olimp/examples/precompensation/tennenholtz_zachevsky.py

По структуре код аналогичен используемому в методе Achromatic Daltonization (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation.tennenholtz_zachevsky

## Предкомпенсация нейросетевыми методами

### Предкомпенсация рефракционных искажений (РИЗ)

#### Метод DWDN (Deep Wiener Deconvolution Network)

Метод **DWDN** — нейросетевой алгоритм предкомпенсации,  
построенный на архитектуре **глубокой деконволюционной сети**,  
которая приближает работу **фильтра Винера** в обучаемом виде.  
DWDN учитывает как искажения от аберраций зрения (через PSF),  
так и особенности входного изображения, обеспечивая более высокое качество восстановления.

**Вход:**
- изображение;
- PSF (функция рассеяния точки).

**Выход:**
- предкомпенсированное изображение, нормализованное в диапазоне [0, 1].

📖 Подробнее:  
Метод основан на статье:  
**DWDN: Deep Wiener Deconvolution Network for Non-Blind Image Deblurring**,  
arXiv, 2021.  
[Скачать PDF](https://arxiv.org/pdf/2103.09962)

Для запуска метода используйте следующий код:


    from __future__ import annotations

    from typing import Callable
    import torch
    from torch import Tensor

    from olimp.precompensation._demo import demo
    from olimp.precompensation.nn.models.dwdn import PrecompensationDWDN

    if __name__ == "__main__":

        def demo_dwdn(
            image: Tensor, psf: Tensor, progress: Callable[[float], None]
        ) -> Tensor:
            model = PrecompensationDWDN.from_path(path="hf://RVI/dwdn.pt")

            with torch.inference_mode():
                inputs = model.preprocess(image, psf.to(torch.float32))
                progress(0.1)
                (precompensation,) = model(inputs, **model.arguments(inputs, psf))
                progress(1.0)
                return precompensation

        demo("DWDN", demo_dwdn, mono=True, num_output_channels=3)

Здесь:

- `torch.Tensor` — работа с тензорами в PyTorch;
- `Callable` — тип аннотации из `typing`;
- `demo` — утилиты для демонстрации предкомпенсации изображений.

Обращаем внимание на важность запуска нейросетевых моделей внутри контекст-менеджера torch.inference_mode().

Этот код для удобства внесен в файл olimp/examples/precompensation_nn/dwdn.py и может быть запущен командой 

    python3 -m olimp.examples.precompensation_nn.dwdn

В результате запуска этот вызов выдаст окно с 4 изображениями: визуализацией функции рассеяния точки (ФРТ, PSF), исходным изображением, результатом предкомпенсации и симуляцией, как предкомпенсированное изображением будет видно неидеальной зрительной системой с данной ФРТ. 

### 🧠 Метод USRNet

Метод **USRNet** представляет собой **нейросетевой алгоритм предкомпенсации**,  
основанный на **итеративной деконволюции**. Сеть построена по принципу **развёртывания  
оптимизационного алгоритма**, что позволяет достичь высокой точности восстановления  
деталей изображения при наличии искажений, вызванных аберрациями зрения.

USRNet использует PSF (функцию рассеяния точки) и обучена на синтетических данных,  
включая шум и вариативные уровни искажений, что делает её устойчивой к различным ситуациям.

#### 🧾 Вход:
- изображение;
- PSF (в виде тензора);
- параметры: `scale_factor = 1`, `noise_level = 0`.

#### 📤 Выход:
- предкомпенсированное изображение, восстановленное в RGB и нормализованное.

📖 Подробнее:  
Zhang et al.,  
**Deep Unfolding Network for Image Super-Resolution**,  
CVPR, 2020.  
[Скачать PDF](https://openaccess.thecvf.com/content_CVPR_2020/papers/Zhang_Deep_Unfolding_Network_for_Image_Super-Resolution_CVPR_2020_paper.pdf)


Для вызова используйте код из файла olimp/examples/precompensation_nn/usrnet.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.usrnet





### 🧠 Метод CVAE (Conditional Variational Autoencoder)

Метод **CVAE** представляет собой **нейросетевой алгоритм предкомпенсации**,  
основанный на **условном вариационном автокодировщике**. Сеть обучается моделировать  
распределение предкомпенсированных изображений с учётом PSF (функции рассеяния точки),  
что позволяет генерировать реалистичные изображения, устойчивые к различным видам искажений.

CVAE сочетает в себе генеративную модель и стохастический латентный код,  
что делает его пригодным для задач, где необходимо учитывать неопределённость в данных.

#### 🧾 Вход:
- изображение;
- PSF (в виде 2D тензора);
- (внутренне) — кодировка изображения и PSF в латентное пространство  
  и дальнейшая декодировка в предкомпенсированное изображение.

#### 📤 Выход:
- предкомпенсированное изображение;
- среднее (`mu`) и лог-дисперсия (`logvar`) латентного распределения  
  (используются при обучении и для анализа неопределённости).

📖 Подробнее:  
- Zhiwei Xue et. al,  
**Diffusion Models for Probabilistic Deconvolution of Galaxy Images**,   
[Скачать PDF](https://arxiv.org/pdf/2307.11122)  
- Artidoro Pagnoni et al.,  
**Conditional Variational Autoencoder for Neural Machine Translation**,   
[Скачать PDF](https://arxiv.org/abs/1812.04405)



Для вызова используйте код из файла olimp/examples/precompensation_nn/cvae.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.cvae



### 🧠 Метод VAE (Variational Autoencoder)

Метод **VAE** — это **вариационный автокодировщик**, применённый для задачи предкомпенсации  
зрительных искажений. Он обучается реконструировать предкомпенсированные изображения,  
используя только **изображение и PSF**, без дополнительных условий.

#### 🧾 Вход:
- изображение;
- PSF (в виде 2D тензора);
- модель кодирует вход в латентное представление,  
  которое затем декодируется в предкомпенсацию.

#### 📤 Выход:
- предкомпенсированное изображение;
- параметры латентного распределения (`mu`, `logvar`)  
  (используются при обучении и могут быть применены для анализа неопределённости).

📖 Подробнее:  
- Zhiwei Xue et. al,  
**Diffusion Models for Probabilistic Deconvolution of Galaxy Images**, (Идея взята)  
[Скачать PDF](https://arxiv.org/pdf/2307.11122)  
- Kingma & Welling,  
**Auto-Encoding Variational Bayes**,  
ICLR, 2014.  
[Скачать PDF](https://arxiv.org/pdf/1312.6114) 

Для вызова используйте код из файла olimp/examples/precompensation_nn/vae.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.vae



### 🧠 Метод UNET-B0 (на базе EfficientNet)

Метод **UNET-B0** — это модифицированная версия классического U-Net,  
в которой энкодер построен на основе **EfficientNet-B0**.  
Он применяется для задачи предкомпенсации зрительных искажений,  
используя изображение и **PSF** как вход.

#### 🧾 Вход:
- изображение;
- PSF (в виде 2D тензора);
- оба тензора объединяются и подаются на вход сети.

#### 📤 Выход:
- предкомпенсированное изображение  
  (тензор того же размера, что и вход).

📖 Подробнее:  
- Модель построена на основе EfficientNet-B0 (энкодер);  
- Структура декодера соответствует архитектуре U-Net;  
- Модификация для предкомпенсации: *наша реализация без публикации*.  
- Имеет малое количество параметров при высокой точности.

Для вызова используйте код из файла olimp/examples/precompensation_nn/unet_efficient_b0.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.unet_efficient_b0



### 🧠 Метод UNETVAE

Метод **UNETVAE** сочетает в себе преимущества UNet и вариационного автокодировщика (VAE),  
что позволяет моделировать неопределённость и сохранять высокое качество восстановления.  
Модель принимает на вход изображение и **PSF**, извлекает латентное распределение и  
восстанавливает предкомпенсированное изображение.

#### 🧾 Вход:
- изображение;
- PSF (в виде 2D тензора);
- данные кодируются в `mu`, `logvar`, затем реконструируются через выборку из латентного распределения.

#### 📤 Выход:
- предкомпенсированное изображение;
- параметры латентного распределения (`mu`, `logvar`)  
  (используются в процессе обучения и могут быть полезны для анализа).

📖 Подробнее:  
- Архитектура энкодера-декодера построена на основе UNet;  
- Добавлен стохастический латентный слой, как в VAE;  
- Модификация для предкомпенсации: *наша реализация без публикации*.



Для вызова используйте код из файла olimp/examples/precompensation_nn/unetvae.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.unetvae


### 🧠 Метод VDSR (Very Deep Super-Resolution)

Метод **VDSR** — это **глубокая сверточная нейросеть**, адаптированная для задачи  
предкомпенсации зрительных искажений. Исходная архитектура VDSR была разработана для  
сверхразрешения изображений, но в нашей работе она модифицирована для работы с PSF  
(функцией рассеяния точки) и генерации предкомпенсированных изображений.

VDSR использует простую, но эффективную архитектуру с множеством сверточных слоёв,  
что позволяет ей точно восстанавливать детали изображения даже при искажениях.

#### 🧾 Вход:
- изображение;
- PSF (в виде 2D тензора);
- данные обрабатываются и подаются на вход сверточной сети.

#### 📤 Выход:
- предкомпенсированное изображение.

📖 Подробнее:  
- Базовая архитектура:  
  Kim et al.,  
  **Accurate Image Super-Resolution Using Very Deep Convolutional Networks**,  
  CVPR, 2016.  
  [Скачать PDF](https://arxiv.org/pdf/1511.04587)

- Модификация для предкомпенсации: *наша реализация без публикации*.


Для вызова используйте код из файла olimp/examples/precompensation_nn/unetvae.py

По структуре код аналогичен используемому в методе DWDN (см. выше). Для его быстрого запуска используйте команду:

    python3 -m olimp.examples.precompensation_nn.vdsr


## 🧠 Метод CVDSwin4Channels

Метод **CVDSwin4Channels** является нашей модификацией, основанной на семействе нейросетей CVD-SWIN (ссылка приведена ниже).
CVD-SWIN представляет собой семейство нейросетевых архитектур, основанных на Swin трансформерах и предназначенных для предкомпенсации цветовых искажений, вызванных дефектами цветового зрения (ДЦЗ).
Используемая функция потерь учитывает как контраст на изображении, так и "натуральность" цветов.
Однако, данная нейросеть ограничена обучением на одном типе искажения: дейтеранопии или протанопии.

Метод **CVDSwin4Channels** включает в себя параметризованный вход, что позволяет обучать нейросеть одновременно на нескольких типах искажений ДЦЗ.
Это реализовано в виде представления параметра искажения (угол между вектором цветовой слепоты и осью L в цветовом пространстве LMS) в виде четвертого канала, 
представляющего собой попиксельное скалярное произведение преобразованного в пространство linRGB изображения и вектора цветовой слепоты в пространстве linRGB.
Дополнительно внесена модификация, по которой нейросеть для предкомпенсации использует преобразования яркости.
Небольшое изменение яркости возникает на этапе квантильного клипинга, где изображение нормализуется в диапазон [0,1] 
частично путем деления всего итогового linRGB изображения на одинаковое число (определяется квантилем от набора 
максимальных значений среди трех каналов по всем пикселям) и частично прямым клиппингом в [0,1].

Это позволяет произвести предкомпенсацию изображения с сохранением исходных цветов.

#### 🧾 Вход:
- изображение (в RGB, затем преобразуется в 4-канальный формат);
- тип дефекта цветового зрения (например, `protan`, `deutan`, или любое другое заданное углом).

#### 📤 Выход:
- предкомпенсированное изображение, пригодное для восприятия пользователем с ДЦЗ.

Метод **CVDSwin4Channels** является нашей модификацией и еще не опубликована.

📖 Подробнее о CVD-SWIN, на которой основана наша модификация:  
Ligeng Chen et al.,  
**Swin Transformer for Precompensation of Refractive and Color Vision Defects**,  
Neural Computing and Applications, Springer, 2023.  
[Скачать PDF](https://link.springer.com/content/pdf/10.1007/s00521-023-09367-2.pdf)

Для запуска метода используйте следующий код:

    from __future__ import annotations

    from typing import Callable
    import torch
    from torch import Tensor

    from olimp.precompensation._demo_cvd import demo as demo_cvd
    from olimp.precompensation.nn.models.cvd_swin.cvd_swin_4channels import (
        CVDSwin4Channels,
    )
    from olimp.simulate.color_blindness_distortion import ColorBlindnessDistortion

    if __name__ == "__main__":

        def demo_cvd_swin(
            image: Tensor,
            distortion: ColorBlindnessDistortion,
            progress: Callable[[float], None],
        ) -> tuple[torch.Tensor]:
            svd_swin = CVDSwin4Channels.from_path()
            image = svd_swin.preprocess(image, hue_angle_deg=torch.tensor([0.0]))
            progress(0.1)
            precompensation = svd_swin(image)
            progress(1.0)
            return (svd_swin.postprocess(precompensation[0]),)

        distortion = ColorBlindnessDistortion.from_type("protan")
        demo_cvd(
            "CVD-SWIN",
            demo_cvd_swin,
            distortion=distortion,
        )


Здесь:

- `torch.Tensor` — работа с тензорами в PyTorch;
- `ColorBlindnessDistortion` — симуляция дихроматического искажения; 
- `CVDSwin4Channels` — класс нейронной сети;
- `demo_cvd` — утилиты для демонстрации предкомпенсации изображений.

Этот код для удобства внесен в файл  и может быть запущен командой olimp/examples/precompensation_nn/cvd_swin.py

    python3 -m olimp.examples.precompensation_nn.cvd_swin

В результате этого запуска выдается окно с 4 изображениями: исходным, симуляцией его восприятия человеком с ДЦЗ, предкомпенсированным и симуляцией его восприятия.


## Генерация реализаций искажений, симулирующих РИЗ и ДЦЗ

### Генерация реализаций рефракционных искажений (РИЗ)

Для генерации датасета функций рассеяния точки (ФРТ), реализующих рефракционные искажения используется класс **PSFSCADataset** (наследуется от абстрактного класса `DistortionDataset`)  
Модель учитывает сферические и цилиндрические ошибки рефракции, угол астигматизма и диаметр зрачка.

#### 🧾 Параметры конструктора:
- **width**, **height** — размеры выходного ФРТ в пикселях (например, `512×512`).
- **sphere_dpt** — распределение сферической составляющей рефракции (в диоптриях); словарь:
  - `name`: тип распределения, например `"uniform"`
  - `a`, `b`: границы диапазона, например `a = -4.0`, `b = -2.0`
- **cylinder_dpt** — распределение цилиндрической составляющей (в диоптриях); аналогично `sphere_dpt`.
- **angle_deg** — распределение угла астигматизма в градусах; например `a = 0.0`, `b = 180.0`.
- **pupil_diameter_mm** — диаметр зрачка в миллиметрах; например `a = 3.0`, `b = 5.0`.
- **am2px** — коэффициент перевода угловых минут в пиксели (например, `0.001`).
- **seed** — начальное значение генератора случайных чисел для воспроизводимости (например, `42`).
- **size** — количество выборок в датасете (например, `100`).

#### 📥 Как использовать:
1. Создайте экземпляр `PSFSCADataset` с нужными параметрами.
2. Получите элемент через `dataset[idx]`, где `idx` от `0` до `size-1`.
3. Каждый элемент — тензор формы `(1, H, W)` — одномерная ФРТ, сформированная моделью глаза.

#### 📤 Выход каждого элемента:
- **ФРТ**: тензор `Tensor[1, H, W]`, соответствующий смоделированному искажению зрения.
- **Параметры выборки**: `sphere_dpt`, `cylinder_dpt`, `angle_deg`, `pupil_diameter_mm` (можно логгировать отдельно).

Пример использования:
    from __future__ import annotations

    from torch import Tensor
    from matplotlib import pylab as plt

    from olimp.precompensation.nn.dataset.psf_sca import PSFSCADataset
    from olimp.simulate._demo_distortion import demo


    def show_one(image: Tensor, title: str) -> None:
        if image.isnan().any():
            raise ValueError("has nan")
        fig, ax1 = plt.subplots(dpi=72, figsize=(6, 4.5), ncols=1, nrows=1)
        plt.title(title)
        ax1.imshow(image)
        plt.show()


    if __name__ == "__main__":

        dataset = PSFSCADataset(
            width=512,
            height=512,
            sphere_dpt={
                "name": "uniform",
                "a": -4.0,
                "b": -2.0,
            },  # uniform в диапазоне [-2, 0]
            cylinder_dpt={
                "name": "uniform",
                "a": -4.0,
                "b": -2.0,
            },  # то, что у вас уже было
            angle_deg={
                "name": "uniform",
                "a": 0.0,
                "b": 180.0,
            },  # то, что у вас уже было
            pupil_diameter_mm={
                "name": "uniform",
                "a": 3.0,
                "b": 5.0,
            },  # uniform, например, от 3 до 5 мм
            am2px=0.001,
            seed=42,
            size=100,
        )

        def demo_simulate():
            apply_fn = dataset.apply()
            funcs = []

            for i in range(3):
                psf = dataset[i]
                show_one(psf[0], title=f"Gaussian PSF #{i}")

                # создаём функцию с захваченным индексом
                funcs.append((lambda image, i=i: list(apply_fn(image))[i], f"{i}"))

            return funcs

        demo("RefractionDistortion", demo_simulate, on="horse", size=(512, 512))

Для удобства этот код размещен в файле olimp/examples/simulate/psf_sca_datasets.py и может быть запущен командой:

    python3 -m olimp.examples.simulate.psf_sca_datasets

В результате запуска в памяти будет сформирован датасет размером 100 (параметр size) и открыты 3 окна с примерами ФРТ из этого датасета, а также окно с примерами симуляций РИЗ (размытыми при помощи этих ФРТ изображений). Окна будут открываться последовательно.


### Генерация реализаций дихроматических искажений (ДЦЗ)

Для генерации датасета направлений цветовой слепоты, описывающих разные виды дихромазии, используется класс **ColorBlindnessDataset** (наследуется от абстрактного класса `DistortionDataset`)  
Помимо стандартных протанопов, дейтеранопов и тританопов модель поддерживает промежуточные направления цветовой слепоты.

#### Параметры конструктора:
  - **angle_deg** — распределение угла на цветовом круге (в градусах):
  - `name`: тип распределения (например, `"uniform"`)
  - `a`: нижняя граница диапазона (например, `33.0`)
  - `b`: верхняя граница диапазона (например, `360.0`)
- **seed** — значение для инициализации генератора случайных чисел (например, `11`)
- **size** — требуемый размер датасета (например, `365`)

#### 📥 Как использовать:
1. Создайте экземпляр `ColorBlindnessDataset` с нужными параметрами.
2. Получите угол через `angle = dataset[idx].item()`, где `idx` от `0` до `size - 1`.
3. Получите функцию искажения через `dataset._distortions[idx]()`.
4. Примените её к изображению: `image_transformed = apply_fn(image)`.

#### 📤 Выход каждого элемента:
- **Угол цветовой слепоты**: значение типа `float`, в градусах.
- **Функция искажения**: `Callable[[Tensor], Tensor]`, имитирующая дихромазию с заданным углом.

Пример использования:

    from __future__ import annotations

    from olimp.precompensation.nn.dataset.cvd_angle import ColorBlindnessDataset
    from olimp.simulate._demo_distortion import demo


    if __name__ == "__main__":

        dataset = ColorBlindnessDataset(
            angle_deg={"name": "uniform", "a": 33.0, "b": 360.0}, seed=11, size=365
        )

        def demo_simulate():
            funcs = []

            for i in range(3):
                angle = dataset[i].item()
                funcs.append(
                    (
                        lambda image, distortion=dataset._distortions[
                            i
                        ]: distortion()(image),
                        f"{angle:.1f}°",
                    )
                )

            return funcs

        demo("ColorBlindnessDistortion (3 angles)", demo_simulate)

Для удобства данный пример сохранен в файл olimp/examples/simulate/color_blind_distortion_datasets.py и может быть запущен командой

    python3 -m olimp.examples.simulate.color_blind_distortion_datasets 

В результате запуска в памяти будет сформирован датасет из 365 (параметр size) направлений цветовой слепоты и открыто окно, в котором демонстрируются изображение и примеры его дихроматических искажений с 3 направлениями из этого датасета.

## Обучение представленных во фреймворке нейросетевых архитектур с заданным датасетом

Представленные во фреймворке нейросетевые архитектуры могут быть заново обучены с особыми параметрами. Для этого необходимо сформировать конфигурационный файл обучения следующего вида:

    {
        "model": {
            "name": "precompensationusrnet",
            "n_iter": 2
        },
        "img": {
            "datasets": [
                {
                    "name": "SCA2023",
                    "subsets": [
                        "Images/Real_images/Faces"
                    ]
                }
            ],
            "transforms": [
                {
                    "name": "grayscale",
                    "num_output_channels": 3
                },
                {
                    "name": "resize",
                    "width": 512,
                    "height": 512
                },
                {
                    "name": "float32"
                },
                {
                    "name": "divide",
                    "value": 255
                }
            ]
        },
        "distortion": [
            {
                "name": "refraction_datasets",
                "psf": {
                    "datasets": [
                        {
                            "name": "SCA2023",
                            "subsets": [
                                "PSFs/Narrow"
                            ]
                        }
                    ]
                }
            }
        ],
        "batch_size": 1,
        "sample_size": 1,
        "epochs": 500,
        "optimizer": {
            "name": "Adam",
            "learning_rate": 0.0001,
            "eps": 1e-8
        },
        "loss_function": {
            "name": "MS_SSIM"
        }
    }

Данная конфигурация размещена в файле olimp/precompensation/nn/pipeline/usrnet.json

Для обучения с данной конфигурацией используйте команду (находясь в корневой директории проекта или указав полный путь к файлу конфигурации):

    python3 -m olimp.precompensation.nn.train.train --config ./olimp/precompensation/nn/pipeline/usrnet.json

В результате выполнения этой команды автоматически скачивается требуемый для обучения датасет, выполняется обучения и веса обученной нейросетевой модели помещаются во временную директорию внутри **epoch_saved/** 