CAS (computer algebra system) 的算法、实现及应用
计算机代数系统的算法、实现及应用：基于符号执行技术的文献综述
引言
计算机代数系统（Computer Algebra System，CAS）传统上指专门用于符号数学计算的软件系统，如Mathematica、Maple、Maxima等，它们能够执行代数运算、符号积分、方程求解等数学操作[1]。然而，随着计算机科学的发展，“符号计算”的概念已扩展到更广泛的程序符号分析领域，其中符号执行（Symbolic Execution）技术成为现代软件验证和测试的核心方法[3]。符号执行通过将程序输入抽象为符号值，系统地探索程序执行路径，本质上是一种对程序行为进行符号推理的计算过程[5]。

本综述旨在从符号执行技术的视角，重新审视现代计算机代数系统的算法设计、系统实现和应用实践。尽管传统CAS关注数学表达式处理，而符号执行聚焦程序分析，但两者在符号推理、约束求解和自动化验证等方面存在深刻的内在联系[12]。符号执行框架可视为一类特殊的符号计算系统，专门用于程序的形式化分析和正确性验证[13]。

近年来，随着软件复杂度的增加和安全性要求的提高，符号执行技术得到了快速发展。从早期的单一路径探索到现在的并行符号执行[6]、混合符号执行[10, 25]和神经增强符号执行[19]，该领域已形成了丰富的算法体系和技术架构。同时，符号执行在智能合约安全[7]、物联网协议验证[9]、操作系统漏洞检测[21]等领域的成功应用，展现了其作为工程化符号计算系统的强大潜力[15]。

本文综述将围绕以下结构展开：第二章分析符号执行核心算法的研究进展；第三章探讨符号执行系统的实现架构与技术选型；第四章总结符号执行在科学计算与工程实践中的应用案例；最后第五章提出未来研究方向与挑战。

2. CAS核心算法研究进展
2.1 符号执行的基本算法框架
符号执行的核心算法基于路径条件的构造与求解。传统符号执行通过将程序输入抽象为符号变量，在程序执行过程中累积分支条件，形成路径约束[27]。然而，这种方法面临路径爆炸问题的严重挑战[29]。为解决这一问题，研究者提出了多种改进算法，例如将静态分析、程序切片与符号执行相结合并引入混合执行技术[25]。

动态符号执行（DSE）结合具体执行与符号执行，通过动态插桩技术减少路径探索数量[32]。Zhang等人提出的多路复用符号执行（Multiplex Symbolic Execution，MuSE）创新性地将约束求解过程映射到路径探索，实现“一次求解，多路探索”，显著提高了执行效率[29]。这一方法通过利用约束求解器中的中间赋值生成新程序输入，将符号执行中的双重搜索过程统一起来。

在约束求解优化方面，Shuai等人提出了基于部分解的约束求解缓存方法，利用约束求解过程中的部分解生成更多缓存条目，提高缓存命中率[17]。实验表明，该方法在KLEE和Symbolic PathFinder上实现了1.07倍到2.3倍的速度提升。

2.2 路径探索与剪枝策略
路径选择策略直接影响符号执行的效率和覆盖率。Sabbaghi等人对动态符号执行中的搜索策略进行了系统综述，指出启发式搜索、随机搜索和混合搜索是三种主要策略类型[32]。其中，基于程序覆盖率的启发式搜索在实践中应用最广泛。

近年来，机器学习技术被引入路径剪枝。Molina等人提出了基于学习的不可行路径剪枝方法，通过神经网络识别部分具体堆结构的可行性，自动检测路径不可行性，无需手动提供可行性检查例程[26]。实验表明，该方法在基于堆的数据结构基准测试中显著提高了符号执行的运行时间。

Yi等人进一步提出了兼容分支覆盖驱动的符号执行，通过程序依赖分析获得新颖的路径剪枝策略[18]。该方法基于兼容分支集，引导符号执行探索可行分支，同时稳妥地剪枝对分支覆盖无新贡献的冗余路径。在GNU Coreutils程序上的实验显示，该方法平均减少了45%的路径和3倍的加速。

2.3 约束求解的智能化改进
约束求解是符号执行的主要性能瓶颈。针对基于堆的程序，有研究引入分离逻辑来增强符号执行，以更精确地建模堆操作并生成测试输入[28]。Wen等人提出了智能约束分类方法ICON，利用神经网络对路径条件进行可满足性分类，在不需要具体解时使用快速分类代替耗时的约束求解[19]。实验评估显示，ICON在分类路径条件方面具有高准确性，比传统约束求解技术更快。

Li等人早在2016年就探索了机器学习驱动的约束求解，通过机器学习模型辅助符号执行处理复杂程序[27]。这种方法减少了直接调用约束求解器的次数，特别是在处理非线性约束时表现出优势。

具体约束引导的符号执行是另一个创新方向。Sun等人发现，符号执行致力于覆盖所有符号分支，而具体分支常被忽略，引导符号执行向未覆盖的具体分支发展有潜力提高整体代码覆盖率[16]。实验证明，该方法提高了KLEE在10个开源C程序上的代码覆盖率和安全违规发现能力。

2.4 并行与分布式符号执行
并行化是提升符号执行可扩展性的重要途径。Wei等人提出了Gensym，一个优化符号执行编译器，通过将符号执行任务编译为基于连续传递风格的协作并发，实现高效的并行化[6]。Gensym基于部分求值和生成式编程技术，在20个基准程序上实现了平均4.6倍的顺序执行加速和9.4倍的并行执行加速。

He等人专门针对智能合约漏洞检测，提出了并行简化符号执行（ParSE）方法，通过并行化和简化技术提高检测效率和真阳性率[15]。实验表明，ParSE将Oyente和Mythril的检测速度分别提高了9.33倍和5.30倍。

在硬件加速方面，Cisneros-Garibay等人开发的Pyrometheus提供了符号抽象，支持在计算加速器（如GPU）上执行，并实现自动微分[11]。该工具通过代码生成从热化学机理的符号表示生成多种目标语言代码，包括Python、C++和Fortran，同时保留热化学的符号表示。

2.5 混合与组合分析方法
混合符号执行结合了静态分析和符号执行的优势。Aslanyan等人提出了结合静态分析与定向符号执行的内存泄漏检测方法，首先使用上下文、流和字段敏感的静态分析识别潜在内存泄漏，然后通过定向符号执行提供路径敏感性并过滤误报[10]。该方法在MLH工具中实现，在OpenSSL、FFmpeg等开源软件中发现了多个已确认的漏洞。类似地，Symbiotic 8等工具也扩展了静态分析、插桩、切片与符号执行的组合，并引入了混合符号执行等新技术。

组合符号执行支持正确性和错误性推理。Lööw等人开发了组合符号执行框架，能够同时进行程序正确性验证和错误检测[20]。这种组合方法提供了更全面的程序分析能力。

静态分析引导的符号执行（STASE）专门针对UEFI漏洞检测，首先进行基于规则的静态漏洞分析识别潜在目标，然后集中符号执行资源进行精确检测和特征生成[21]。该方法在Tianocore的EDKII代码库中检测到13个新漏洞。

2.6 CAS场景特殊性：符号执行与传统符号计算的算法差异
与传统计算机代数系统的符号计算不同，符号执行处理的“符号”是程序变量的抽象表示，而非数学表达式。这导致算法设计上的根本差异：符号执行算法必须处理程序状态、内存模型和控制流等计算特征，而传统CAS算法主要处理代数结构和数学变换。然而，两者在约束求解和逻辑推理方面有共同的技术基础，如SMT求解器在符号执行中的广泛应用与在CAS方程求解中的应用共享相同的数学原理。

3. CAS系统实现与技术架构
3.1 符号执行引擎的实现架构
现代符号执行系统的实现架构通常采用模块化设计，将符号执行引擎、约束求解器、路径管理和用户接口分离。Horváth等人详细分析了Clang静态分析器和CodeChecker框架的架构设计，强调了端到端可扩展性的重要性[13]。该架构包括分析运行时间和内存消耗、错误呈现、自动误报抑制、增量分析和持续集成循环等多个组件。

编译型符号执行是一种创新的实现方式。Wei等人的Gensym采用编译和代码生成技术，将符号执行任务编译为可并行执行的代码，避免了传统解释型实现的性能开销。这种方法的关键见解是将符号执行任务通过连续传递风格编译为协作并发，从而启用高效并行。

3.2 语言支持与可扩展性
符号执行系统需要支持多种编程语言和运行环境。Amadini等人研究了JavaScript动态符号执行的约束编程方法，解决了JavaScript语言特性的挑战[30]。Smith等人开发的Icarus框架专注于即时编译器的可信验证，通过符号元执行技术编码所有可能JIT生成程序的行为为单个Boogie元程序，可被SMT求解器高效验证[23]。

在语言扩展方面，Lin等人提出了符号执行博弈语义，支持高阶程序和外部方法的符号执行和模型检查[33]。该框架结合传统符号执行技术与操作博弈语义，构建了能够捕获任意外部行为的符号执行语义。

3.3 工具集成与生态系统
成熟的符号执行系统往往集成到更广泛的开发工具链中。Hentschel等人开发的符号执行调试器（SED）提供了一个交互式平台，支持符号执行、调试、验证等多种功能[31]。该工具通过可视化符号执行过程，降低了技术门槛，提高了可用性。

特征工程自动化是另一个重要研究方向。Yoon等人提出的FeatMaker自动为符号执行搜索策略生成状态特征，利用路径条件作为状态特征的基础，通过专门算法迭代生成和优化特征[22]。在15个开源C程序上的实验显示，FeatMaker比依赖手动设计特征的现有搜索策略实现了平均35.3%更高的分支覆盖率。

3.4 性能优化与资源管理
符号执行系统的性能优化涉及多个层面。Zhang等人实证研究了编译器优化对动态符号执行性能的影响，分析了209个GCC编译标志和73个Clang编译标志[14]。研究发现，尽管某些优化使DSE更快，但大多数优化实际上会减慢DSE速度。正影响主要来自指令数量和程序路径的减少，而负影响则由指令或路径数量增加、库函数内联阻止DSE引擎使用函数摘要以及导致更复杂约束的算术优化等因素引起。

缓存优化是提高约束求解效率的关键技术。Shuai等人的部分解缓存方法通过在约束求解过程中利用中间赋值生成更多缓存条目，自然提高了缓存命中率[17]。这种方法避免了传统缓存方法无法在所有程序上表现良好的问题。

3.5 CAS场景特殊性：符号执行系统的工程化挑战
与传统计算机代数系统相比，符号执行系统的实现面临独特的工程化挑战：首先，必须处理程序语义的复杂性，包括指针操作、动态内存分配和并发控制；其次，需要与现有工具链（如编译器、调试器）深度集成；第三，必须平衡精度与可扩展性，在大规模软件分析中保持实用性能。这些挑战促使符号执行系统采用更灵活的插件架构和模块化设计，不同于传统CAS相对固定的数学内核架构。

4. CAS在科学与工程领域的应用
4.1 软件安全与漏洞检测
符号执行在软件安全领域有广泛应用。Liu等人针对智能合约状态不一致漏洞，提出了基于流分歧和多路符号执行的检测方法DivertScan[7]。该方法首先使用流分歧检查涉及变量可能流向的位置，精确推断数据竞争的潜在影响，然后通过多路符号执行在一次求解中检查不同执行顺序。实验证明该方法显著减少了误报而不引入漏报。

污点分析与符号执行的结合提高了漏洞检测精度。Tang等人提出的TaintSE通过代码覆盖引导符号执行路径探索和测试用例生成，提高了动态污点分析的代码覆盖率[3]。在BugBench测试集上，TaintSE的分析路径覆盖率比动态污点分析工具Libdft提高了24%-35%。

Seto等人则从防御角度研究了防止符号执行攻击的低成本混淆方法，通过数组引用、位旋转和XOR操作的组合，以低计算成本有效防止符号执行攻击[34]。实验使用angr和KLEE作为符号执行工具，验证了该方法的有效性。

4.2 测试用例生成与质量保障
符号执行是自动化测试用例生成的核心技术。Wu等人提出了自然符号执行，考虑输入的自然性生成测试数据，通过用户提供的输入语义大幅增强输入的自然性，同时保留强大的错误发现潜力[8]。在大数据应用上，NaturalSym比最先进的DISC符号执行器BigTest检测到1.29倍注入的故障。对于基于堆的程序，利用分离逻辑增强符号执行也被证明能有效生成测试输入[28]。

Sun等人开发的ReMuSSE基于选择性符号执行识别冗余变异体，通过识别涉及变异语句的程序块内具有相似程序执行状态变化的变异体来揭示冗余变异体[4]。在13个C程序的实证研究中，ReMuSSE识别了高达31.4%的冗余变异体，从而节省了高达35.2%的弱变异测试时间成本。

状态一致性测试是另一个重要应用。Tempel等人提出了基于规范的符号执行，用于物联网中的状态网络协议实现测试，通过创建协议状态和消息格式规范来缓解状态空间爆炸问题[9]。该方法在两个流行物联网操作系统的协议实现测试中实现了代码覆盖率的显著提高，并在RIOT操作系统中发现了三个关键且先前未知的错误。

4.3 形式化验证与正确性证明
符号执行在形式化验证中发挥关键作用。Zimmerman等人提出了声音渐进验证，结合静态和动态检查支持显式部分规范的验证[5]。该方法将符号执行、优化的运行时检查生成和运行时执行形式化，并证明其声音性，覆盖了Viper工具的核心子集。

Tiraboschi等人探索了通过抽象解释的声音符号执行及其在安全中的应用，通过结合符号执行和抽象解释获得两全其美的效果[12]。RedSoundRSE分析既提供语义声音结果，又能够推导出有界内的反例轨迹对。

组合验证提供了更全面的保证。Lööw等人的组合符号执行支持正确性和错误性推理，为程序验证提供双重保障[20]。这种方法特别适合需要高可靠性的关键系统。

4.4 特定领域应用
符号执行在多个专业领域得到成功应用。Bannour等人将符号执行用于自动驾驶汽车验证的逻辑场景生成，通过离散化和符号算术的紧凑模型表示，以及专门的符号执行技术，生成覆盖真实情况的场景[24]。该方法在3SA项目的真实自动驾驶黑盒模块上进行了评估。

在数值计算领域，Virtanen等人开发的SciPy 1.0提供了科学计算的基本算法，虽然主要关注数值计算，但其架构设计体现了现代科学计算软件的系统化思路[1]。Harris等人的NumPy数组编程框架则展示了高效数值计算的基础设施设计[2]。

燃烧动力学计算是一个特殊应用领域。Cisneros-Garibay等人的Pyrometheus通过符号抽象支持在计算加速器上执行燃烧动力学和热力学计算，并实现自动微分[11]。该方法分离了计算关注点：生成的代码处理数组值表达式但不指定其语义，这些语义由兼容的数组库（如NumPy、Pytato和Google JAX）提供。

4.5 CAS场景特殊性：符号执行应用的工程实践挑战
与传统计算机代数系统在教育、科研等领域的应用不同，符号执行技术主要应用于软件工程实践中，面临更严格的实用性要求和性能约束。在实际工程应用中，符号执行工具必须：1) 处理工业级代码规模；2) 提供可操作的结果（如具体测试用例或漏洞利用）；3) 集成到现有开发流程中。这些要求推动了符号执行技术向增量分析、交互式调试和持续集成等方向发展，形成了与传统CAS不同的应用生态。

5. 结论与未来研究方向
5.1 研究总结
本文综述了基于符号执行技术的现代计算机代数系统在算法、实现和应用三个方面的研究进展。从算法层面看，符号执行已从基础的路径探索发展为融合机器学习[26]、并行计算和混合分析的复杂算法体系，并不断引入如分离逻辑等新技术以应对特定领域的挑战。在实现架构上，现代符号执行系统采用模块化设计、编译优化和工具集成[31]等策略，提高了系统的可扩展性和实用性。在应用实践方面，符号执行已成功应用于软件安全、测试生成[8, 18]和形式验证等多个领域，展现了作为工程化符号计算系统的强大潜力。

然而，当前研究仍存在明显不足：首先，符号执行技术主要关注程序分析，与传统数学符号计算的交叉研究相对较少；其次，大规模实际应用的性能瓶颈仍未完全解决，特别是路径爆炸和约束求解复杂度问题；第三，符号执行系统的易用性和可访问性仍有待提高，限制了技术的广泛采纳。

5.2 未来研究方向
基于当前研究现状和挑战，未来研究方向应集中在以下三个核心领域：

5.2.1 跨领域算法融合与优化
未来的符号执行算法需要更深入地融合传统符号计算技术，特别是在约束求解和逻辑推理方面。应探索数学代数系统与程序分析系统的协同工作框架，利用CAS的强大数学能力增强符号执行的推理能力。同时，需要进一步优化并行符号执行算法，特别是针对异构计算架构（如GPU、TPU）的专门优化，以应对日益增长的计算需求。

5.2.2 系统架构的工程化与标准化
符号执行系统需要向更工程友好的架构发展。重点包括：1) 增量分析支持，允许在代码变更后只重新分析受影响部分；2) 交互式接口设计，降低技术使用门槛；3) 标准化输出格式，便于与其他工具集成。此外，应建立符号执行系统的性能评估基准，提供统一的比较框架，推动技术的系统性改进。

5.2.3 应用场景的拓展与深化
符号执行技术应扩展到更多专业领域。在科学计算中，可探索符号执行与数值计算库（如SciPy、NumPy）的深度融合，实现计算过程的自动验证[2]。在工程实践中，需要开发面向特定领域（如物联网、区块链、自动驾驶）的专用符号执行工具，提高技术的实用性和针对性[24]。同时，应加强符号执行在教育和研究中的应用，培养更广泛的用户基础。

5.3 技术挑战与机遇
符号执行作为现代计算机代数系统的一种表现形式，既面临技术挑战，也蕴含重要发展机遇。主要挑战包括：处理复杂程序语义的固有困难、平衡精度与效率的永恒矛盾、以及适应新兴计算范式的持续需求。同时，随着人工智能技术的发展，神经符号计算为符号执行提供了新的增强路径；云计算和边缘计算的普及，则为分布式符号执行创造了基础设施条件。

未来的符号执行系统应当向智能化、云原生和领域专用方向发展，既保持符号推理的严谨性，又提高工程实践的实用性，最终形成新一代的计算机代数基础设施，为软件可靠性和安全性提供坚实保障。

参考文献
[1] Pauli Virtanen, Ralf Gommers, Travis E. Oliphant, 等. SciPy 1.0: fundamental algorithms for scientific computing in Python[J]. Nature Methods, 2020. DOI: https://doi.org/10.1038/s41592-019-0686-2

[2] Charles R. Harris, K. Jarrod Millman, Stéfan J. van der Walt, 等. Array programming with NumPy[J]. Nature, 2020. DOI: https://doi.org/10.1038/s41586-020-2649-2

[3] Chenghua Tang, Xiaolong Guan, Mengmeng Yang, 等. TaintSE: Dynamic Taint Analysis Combined with Symbolic Execution and Constraint Association[C]//2023 IEEE 14th International Conference on Software Engineering and Service Science (ICSESS). 2023. DOI: 10.1109/ICSESS58500.2023.10293040

[4] Chang-ai Sun, An Fu, Xin Guo, 等. ReMuSSE: A Redundant Mutant Identification Technique Based on Selective Symbolic Execution[C]//IEEE Transactions on Reliability. 2022. DOI: 10.1109/tr.2020.3011423

[5] Conrad Zimmerman, Jenna DiVincenzo, Jonathan Aldrich. Sound Gradual Verification with Symbolic Execution[C]//Proceedings of the ACM on Programming Languages. 2023. DOI: 10.1145/3632927

[6] Guannan Wei, Songlin Jia, Ruiqin Gao, 等. Compiling Parallel Symbolic Execution with Continuations[C]//2023 IEEE/ACM 45th International Conference on Software Engineering (ICSE). 2023. DOI: 10.1109/ICSE48619.2023.00116

[7] Yinxi Liu, Wei Meng, Yinqian Zhang. Detecting Smart Contract State-Inconsistency Bugs via Flow Divergence and Multiplex Symbolic Execution[C]//Proceedings of the ACM on Software Engineering. 2025. DOI: 10.1145/3715712

[8] Yaoxuan Wu, Ahmad Humayun, Muhammad Ali Gulzar, 等. Natural Symbolic Execution-Based Testing for Big Data Analytics[C]//Proceedings of the ACM on Software Engineering. 2024. DOI: 10.1145/3660825

[9] Sören Tempel, V. Herdt, R. Drechsler. Specification-Based Symbolic Execution for Stateful Network Protocol Implementations in IoT[C]//IEEE Internet of Things Journal. 2023. DOI: 10.1109/JIOT.2023.3236694

[10] H. Aslanyan, Hovhannes Movsisyan, Hripsime Hovhannisyan, 等. Combining Static Analysis With Directed Symbolic Execution for Scalable and Accurate Memory Leak Detection[C]//IEEE Access. 2024. DOI: 10.1109/ACCESS.2024.3409838

[11] Esteban Cisneros-Garibay, H. L. Berre, Spencer H. Bryngelson, 等. Pyrometheus: Symbolic abstractions for XPU and automatically differentiated computation of combustion kinetics and thermodynamics[J]. Comput. Phys. Commun., 2025. DOI: 10.1016/j.cpc.2025.109987

[12] Ignacio Tiraboschi, Tamara Rezk, Xavier Rival. Sound Symbolic Execution via Abstract Interpretation and its Application to Security[J]. ArXiv, 2023. DOI: 10.1007/978-3-031-24950-1_13

[13] Gábor Horváth, Réka Kovács, Zoltán Porkoláb. Scaling Symbolic Execution to Large Software Systems. arXiv preprint arXiv:2408.01909

[14] Yue Zhang, Melih Sirlanci, Ruoyu Wang, 等. When Compiler Optimizations Meet Symbolic Execution: An Empirical Study[C]//Proceedings of the 2024 on ACM SIGSAC Conference on Computer and Communications Security. 2024. DOI: 10.1145/3658644.3670372

[15] Long He, Xiangfu Zhao, Yichen Wang. ParSE: Efficient Detection of Smart Contract Vulnerabilities via Parallel and Simplified Symbolic Execution[C]//2024 IEEE/ACM 46th International Conference on Software Engineering: Companion Proceedings (ICSE-Companion). 2024. DOI: 10.1145/3639478.3643066

[16] Yue Sun, Guowei Yang, Shichao Lv, 等. Concrete Constraint Guided Symbolic Execution[C]//2024 IEEE/ACM 46th International Conference on Software Engineering (ICSE). 2024. DOI: 10.1145/3597503.3639078

[17] Ziqi Shuai, Zhenbang Chen, Kelin Ma, 等. Partial Solution Based Constraint Solving Cache in Symbolic Execution[C]//Proceedings of the ACM on Software Engineering. 2024. DOI: 10.1145/3660817

[18] Qiuping Yi, Yifan Yu, Guowei Yang. Compatible Branch Coverage Driven Symbolic Execution for Efficient Bug Finding[C]//Proceedings of the ACM on Programming Languages. 2024. DOI: 10.1145/3656443

[19] Junye Wen, Tarek Mahmud, Meiru Che, 等. Intelligent Constraint Classification for Symbolic Execution[C]//2023 IEEE International Conference on Software Analysis, Evolution and Reengineering (SANER). 2023. DOI: 10.1109/SANER56733.2023.00023

[20] Andreas Lööw, Daniele Nantes-Sobrinho, Sacha-Élie Ayoun, 等. Compositional Symbolic Execution for Correctness and Incorrectness Reasoning (Artifact)[J]. Dagstuhl Artifacts Ser., 2024. DOI: 10.4230/DARTS.10.2.13

[21] Md Shafiuzzaman, Achintya Desai, Laboni Sarker, 等. STASE: Static Analysis Guided Symbolic Execution for UEFI Vulnerability Signature Generation*[C]//2024 39th IEEE/ACM International Conference on Automated Software Engineering (ASE). 2024. DOI: 10.1145/3691620.3695543

[22] Jaehan Yoon, Sooyoung Cha. FeatMaker: Automated Feature Engineering for Search Strategy of Symbolic Execution[C]//Proceedings of the ACM on Software Engineering. 2024. DOI: 10.1145/3660815

[23] Naomi Smith, Abhishek Sharma, John Renner, 等. Icarus: Trustworthy Just-In-Time Compilers with Symbolic Meta-Execution[C]//Proceedings of the ACM SIGOPS 30th Symposium on Operating Systems Principles. 2024. DOI: 10.1145/3694715.3695949

[24] Boutheina Bannour, Julien Niol, Paolo Crisafulli. Symbolic Model-based Design and Generation of Logical Scenarios for Autonomous Vehicles Validation[C]//2021 IEEE Intelligent Vehicles Symposium (IV). 2021. DOI: 10.1109/iv48863.2021.9575528

[25] Marek Chalupa, Tomás Jasek, Jakub Novák, 等. Symbiotic 8: Beyond Symbolic Execution[J]. Tools and Algorithms for the Construction and Analysis of Systems, 2021. DOI: 10.1007/978-3-030-72013-1_31

[26] F. Molina, Pablo Ponzio, Nazareno Aguirre, 等. Learning to Prune Infeasible Paths in Generalized Symbolic Execution[C]//2022 IEEE 33rd International Symposium on Software Reliability Engineering (ISSRE). 2022. DOI: 10.1109/ISSRE55969.2022.00054

[27] Xin Li, Yongjuan Liang, Hong Qian, 等. Symbolic execution of complex program driven by machine learning based constraint solving[C]//2016 31st IEEE/ACM International Conference on Automated Software Engineering (ASE). 2016. DOI: 10.1145/2970276.2970364

[28] Long H. Pham, Quang Loc Le, Quoc-Sang Phan, 等. Enhancing Symbolic Execution of Heap-based Programs with Separation Logic for Test Input Generation. 2017. DOI: 10.1007/978-3-030-31784-3_12

[29] Yufeng Zhang, Zhenbang Chen, Ziqi Shuai, 等. Multiplex Symbolic Execution: Exploring Multiple Paths by Solving Once[C]//2020 35th IEEE/ACM International Conference on Automated Software Engineering (ASE). 2020. DOI: 10.1145/3324884.3416645

[30] R. Amadini, Mak Andrlon, G. Gange, 等. Constraint Programming for Dynamic Symbolic Execution of JavaScript. 2019. DOI: 10.1007/978-3-030-19212-9_1

[31] Martin Hentschel, Richard Bubel, Reiner Hähnle. The Symbolic Execution Debugger (SED): a platform for interactive symbolic execution, debugging, verification and more. 2019. DOI: 10.1007/s10009-018-0490-9

[32] A. Sabbaghi, M. Keyvanpour. A Systematic Review of Search Strategies in Dynamic Symbolic Execution[J]. Comput. Stand. Interfaces, 2020. DOI: 10.1016/j.csi.2020.103444

[33] Yu-Yang Lin, N. Tzevelekos. Symbolic Execution Game Semantics. 2020. DOI: 10.4230/LIPIcs.FSCD.2020.27

[34] Toshiki Seto, Akito Monden, Zeynep Yücel, 等. On Preventing Symbolic Execution Attacks by Low Cost Obfuscation[C]//2019 20th IEEE/ACIS International Conference on Software Engineering, Artificial Intelligence, Networking and Parallel/Distributed Computing (SNPD). 2019. DOI: 10.1109/SNPD.2019.8935642