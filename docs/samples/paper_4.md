 CAS的算法、实现及应用

文献统计：文献总数：26篇 | 近5年文献占比：69.2% | 英文文献占比：96.2% | 总被引量：14211次
CAS的算法、实现及应用
CAS（符号执行）算法、实现及应用的文献综述
引言
符号执行（Symbolic Execution）作为程序分析和软件验证的核心技术，自1976年由King首次提出以来，已发展成为现代软件工程中不可或缺的工具[6, 21]。与传统的具体执行不同，符号执行通过将程序输入表示为符号值而非具体数值，系统地探索程序的所有可能执行路径，为软件测试、漏洞检测和程序验证提供了强大的理论基础[8, 23]。随着软件系统复杂性的不断增加，符号执行技术在保障软件质量、提高测试效率方面展现出巨大潜力，特别是在安全关键系统和智能合约审计等领域[14, 19]。
符号执行的核心思想是将程序变量抽象为符号表达式，在执行过程中积累路径条件（path condition），通过约束求解器（如SMT求解器）判断路径的可达性[12, 17]。这一过程能够自动生成高覆盖率的测试用例，发现深层次程序缺陷，同时为程序正确性提供形式化证明[10, 24]。近年来，随着约束求解技术的进步和计算能力的提升，符号执行在学术界和工业界均获得了广泛关注和应用[6, 20]。
本文综述旨在系统梳理符号执行领域的研究进展，重点关注其核心算法、软件实现技术以及在实际应用中的创新。首先，我们将分析符号执行的基础算法和优化技术；其次，探讨不同符号执行引擎的架构设计与实现策略；再次，考察符号执行在软件测试、安全审计等领域的应用实践；最后，总结当前研究的不足并提出未来发展方向。通过这一系统性梳理，我们期望为相关研究者提供全面的领域概览和技术参考。
符号执行核心算法研究进展
符号执行基础算法与语义模型
符号执行的算法基础建立在程序语义的形式化表示之上。传统符号执行通常采用操作语义或指称语义来描述程序的符号行为[13, 21]。Voogd等人提出的组合符号执行语义为符号执行提供了严谨的数学基础，将程序视为一组轨迹的集合，每个轨迹对应特定的替换和路径条件[13]。这种形式化方法不仅增强了符号执行的理论严密性，还为程序验证提供了可靠依据。
在基础算法层面，符号执行的核心挑战在于路径爆炸问题的处理。Lucanu等人提出的通用符号执行框架采用共归纳方法，为不同编程语言构建统一的符号执行模型。该框架通过抽象解释技术减少状态空间，有效缓解了路径爆炸问题。同时，Trabish等人提出的可重定位寻址模型通过使用符号地址而非具体地址，实现了动态对象表示的调整，显著提高了内存建模的灵活性[22]。
约束求解策略优化
约束求解是符号执行的性能瓶颈，近年来研究者提出了多种优化策略。Chen等人提出了自适应求解策略合成方法，通过将约束分类并为不同类别合成专门的求解策略，显著提升了符号执行的效率[12, 17]。该方法结合离线训练的深度学习模型和在线调优，平衡了策略合成的开销与性能改进，在KLEE和Symbolic Pathfinder等引擎上实现了70%以上的路径和查询数量增长。这一思路与专门针对符号执行约束求解策略合成的研究方向一致。
针对数组约束求解的特定挑战，Shuai等人提出了类型和区间感知的数组约束求解方法[18]。该方法基于整数线性规划预检查数组约束的不可满足性，并通过类型和区间感知的公理生成减少冗余编码。实验结果表明，该方法平均解决了182.56%更多的约束，探索了277.56%更多的路径[18]。Luo等人则从约束求解时间预测角度出发，提出基于机器学习模型的预测方法，通过预测求解时间帮助符号执行引擎决定是否继续当前求解过程，将约束求解效率提高了1.25到3倍[20]。
编译增强型符号执行
传统符号执行通常在解释环境下进行，而编译增强型符号执行通过将符号执行能力编译到目标程序中，显著提升了执行效率。Poeplau等人提出的SymQEMU系统实现了基于编译的二进制符号执行，无需源代码即可分析二进制程序。该系统在QEMU基础上修改目标程序的中间表示，将符号执行能力编译到二进制文件中，在性能上显著优于S2E和QSYM等最先进的二进制符号执行器。
Arusoaie等人进一步提出了带证明承载参数的认证符号执行，通过生成可被外部可信检查器验证的证明对象，确保了符号执行框架的正确性[10]。该方法基于匹配逻辑，将程序配置表示为匹配逻辑模式，算法视为模式转换器，为模式关系生成证明对象，为工业级符号执行工具提供了可信性保障。
混合符号执行方法
为了克服纯符号执行的局限性，研究者提出了多种混合方法。Su等人将符号执行与模型检查相结合，实现了自动化覆盖驱动测试[8]。该方法通过模型检查生成反例，利用符号执行分析反例路径，迭代提高测试覆盖率。SmartAudiTor框架则将大语言模型引导与符号执行验证相结合，形成混合智能合约漏洞审计框架[14]。这种混合方法结合了LLM的语义理解和符号执行的精确分析，提高了漏洞检测的准确性和效率。
符号执行软件实现与技术架构
符号执行引擎架构设计
现代符号执行引擎通常采用模块化架构，将符号执行核心、约束求解器和路径管理器分离。KLEE作为最著名的符号执行引擎之一，采用了LLVM中间表示作为程序分析的基础，实现了高效的路径探索和约束求解。SymQEMU则在QEMU二进制翻译框架基础上构建，通过修改中间表示实现跨架构的符号执行。这种架构设计使得符号执行工具能够适应不同的目标平台和编程语言，其底层技术栈（如LLVM、QEMU）的选择本身也是软件工程中关键的决策，关乎工具的成败[16]。
Lin等人开发的SolSEE是针对Solidity智能合约的源级符号执行引擎，专门设计用于分析以太坊智能合约[19]。该引擎直接处理Solidity源代码，避免了字节码分析的复杂性，能够更精确地识别智能合约中的安全漏洞。SolSEE的架构包括语法分析、符号状态管理和以太坊虚拟机模拟等模块，为智能合约安全审计提供了专用工具。
交互式符号执行调试平台
Hentschel等人开发的符号执行调试器（SED）提供了一个交互式平台，支持符号执行的调试、验证和可视化[23]。SED平台允许用户在符号执行过程中设置断点、检查符号状态、手动指导路径探索，大大降低了符号执行的使用门槛。该平台将符号执行从自动化工具扩展为交互式开发环境，使开发者能够更深入地理解程序行为。
Voogd等人提出的组合符号执行语义不仅提供了理论框架，也为符号执行引擎的实现提供了指导。基于该语义的引擎能够支持更复杂的程序结构，如并发程序和分布式系统，同时保持语义的一致性和可组合性。这种理论指导的实现方法确保了符号执行工具的正确性和可靠性。
性能优化技术
符号执行的性能优化涉及多个层面，包括内存管理、并行计算和约束求解优化。Trabish提出的可重定位寻址模型通过动态调整对象表示，减少了内存建模的开销[22]。该模型允许在分配后修改对象的底层表示，使用符号地址而非具体地址，支持动态对象分区，提高了符号执行的效率。
在约束求解层面，Chen等人提出的自适应求解策略合成方法通过为不同程序定制求解策略，显著提升了求解效率。该方法将符号执行分为两个阶段：第一阶段使用SMT公式在线合成求解策略，第二阶段应用该策略进行约束求解。实验表明，这种方法在Coreutils基准测试中平均增加了74.37%的路径和73.94%的查询。
硬件加速与专用架构
随着符号执行计算需求的增长，硬件加速成为重要的研究方向。Su等人提出了基于异构多核硬件架构FPGA和软件定义硬件的自适应神经加速单元[15]。该研究采用动态规划重新配置软件定义片上系统，加速神经网络处理过程，为符号执行中的约束求解等计算密集型任务提供了硬件加速方案。设计的脉动阵列矩阵乘法单元支持多种数据类型，验证了并行计算的性能[15]。
Cisneros-Garibay等人开发的Pyrometheus通过符号抽象实现跨平台计算和自动微分[9]。该软件包为燃烧热化学开发符号抽象和相应转换，支持在加速器上计算，避免过早细节指定。生成的代码保留热化学的符号表示，可转换为CPU和加速器上的计算，同时支持自动微分，为科学计算中的符号处理提供了高效框架[9]。
符号执行在软件测试与验证中的应用
自动化测试用例生成
符号执行在自动化测试用例生成方面展现出显著优势。Zhou的研究基于符号执行和混合约束求解的测试用例生成方法，通过系统探索程序路径自动生成覆盖多种执行场景的测试用例[26]。这种方法能够发现传统随机测试难以触发的边界条件，提高测试覆盖率。Su等人将符号执行与模型检查结合，实现了覆盖驱动测试，通过迭代分析提高测试的全面性。
Majumdar等人开发的Comment Probe框架虽然主要关注代码注释评估，但其采用的自动化分类方法对测试用例生成有借鉴意义[7]。该框架使用神经网络对代码注释进行分类，评估其对软件维护的有用性，准确率达到86%以上。类似的方法可用于测试用例的优先级排序和选择，提高测试效率[7]。
程序验证与正确性证明
符号执行为程序验证提供了形式化基础。Knoop等人利用符号执行推断经过证明的精确最坏情况执行时间界限，将猜想替换为正面知识[24]。该方法通过符号执行分析程序的所有可能路径，计算可靠的时间界限，为实时系统提供了严格的时序保证。Arusoaie等人提出的带证明承载参数的认证符号执行进一步增强了验证的可信性。
Voogd等人的组合符号执行语义为程序验证提供了严谨的数学框架。该语义将程序视为一组轨迹，每个轨迹有对应的替换和路径条件，能够证明符号执行计算（最弱）前置条件。这一理论结果为程序正确性验证提供了坚实基础，特别是在安全关键系统的形式化验证中。
智能合约安全审计
随着区块链技术的发展，符号执行在智能合约安全审计中发挥着重要作用。Lin等人开发的SolSEE是针对Solidity智能合约的源级符号执行引擎，专门用于检测智能合约中的安全漏洞。该引擎能够分析重入攻击、整数溢出、权限控制等常见漏洞，为智能合约开发者提供安全审计工具。
Wu等人提出的SmartAudiTor框架结合了大语言模型引导和符号执行验证，形成混合智能合约漏洞审计框架。该方法利用LLM的语义理解能力识别潜在漏洞模式，然后使用符号执行进行精确验证，兼顾了检测的广度和深度。这种混合方法在智能合约安全审计中展现出良好前景，特别是面对复杂合约逻辑时。
软件维护与质量评估
符号执行技术也可应用于软件维护和质量评估。Majumdar等人的Comment Probe框架虽然不是直接使用符号执行，但其自动化评估方法为软件质量分析提供了新思路。该框架基于代码与注释相关性设计特征，推断注释是否一致且非冗余，帮助公司制定更好的代码注释策略，清理大型代码库中无用的注释。
Lu等人提出的AI科学家框架展示了自动化科学研究流程，包括生成研究想法、编写代码、执行实验、可视化结果和撰写科学论文[1]。虽然该框架主要面向科学研究，但其自动化代码生成和测试的思想对软件维护有借鉴意义，可能未来可应用于自动化软件重构和优化[1]。
符号执行在科学与工程领域的应用
科学计算与数值模拟
符号执行技术在科学计算领域的应用日益广泛。Cisneros-Garibay等人开发的Pyrometheus通过符号抽象实现燃烧动力学和热力学的自动微分计算。该软件包为燃烧热化学开发符号抽象和转换，支持在CPU和加速器上的计算，同时保留符号表示以支持自动微分。这种方法显著降低了燃烧模拟的成本，特别是化学物种净产生率和混合物热力学的评估。
Thompson等人开发的LAMMPS作为基于粒子的材料建模灵活模拟工具，虽然主要采用分子动力学方法，但其在原子、介观和连续尺度上的模拟能力展示了计算科学中复杂模型的需求[2]。符号执行技术可应用于此类科学模拟软件的验证，确保数值算法的正确性和稳定性。
物理信息系统与神经网络
Cuomo等人综述了基于物理信息神经网络（PINN）的科学机器学习进展，其中符号计算和自动微分技术发挥着关键作用[3]。PINN通过将物理定律编码为神经网络损失函数，解决了偏微分方程等科学计算问题。符号执行技术可用于验证PINN模型的正确性，确保物理约束的准确实施[3]。
Su等人提出的自适应神经加速单元基于异构多核硬件架构FPGA和软件定义硬件，为神经网络处理提供硬件加速。该研究采用动态规划重新配置软件定义片上系统，加速神经网络过程，设计的脉动阵列矩阵乘法单元支持多种数据类型。这种硬件加速方法对符号执行中的约束求解等计算密集型任务有借鉴意义。
工程系统建模与验证
符号执行在工程系统建模和验证中具有重要应用价值。Spiridonov等人开发了光纤陀螺输出信号噪声的分析和计算机软件数学模型[11]。该研究开发了基于基本表达式的两种数学模型，考虑四个基本噪声源，通过比较模拟结果与商业生产光纤陀螺的噪声验证模型正确性，误差不超过10%[11]。符号执行技术可用于此类工程模型的验证，确保数学模型的正确实现。
Zhang等人研究了随机激光设计和FDTD软件在红外波长下的特征验证[25]。该研究涉及数值模拟软件的验证，符号执行技术可应用于此类工程软件的测试，确保数值算法的正确性和边界条件的正确处理。
科学发现与知识构建
符号执行相关技术也促进了科学发现和知识构建。Lu等人提出的AI科学家框架实现了全自动科学发现，使大语言模型能够独立进行研究并交流发现。该框架生成新颖研究想法、编写代码、执行实验、可视化结果、撰写完整科学论文，并运行模拟评审过程进行评估。每个想法的实施和论文撰写成本低于15美元，展示了自动化科学研究流程的潜力。
Luan等人提出了用于科学知识图谱构建的多任务实体、关系和共指识别方法[4]。该研究虽然不直接使用符号执行，但其信息提取和知识表示方法与符号执行中的程序分析技术有相通之处，都为复杂系统的理解和分析提供了结构化方法[4]。
结论与未来方向
研究总结
符号执行作为程序分析和软件验证的核心技术，在过去几十年中取得了显著进展。从基础算法到实际应用，从理论研究到工程实现，符号执行已发展成为保障软件质量、提高测试效率的重要手段。本综述系统梳理了符号执行的核心算法、软件实现和实际应用，展示了该技术的多样性和广泛适用性。
在算法层面，自适应求解策略合成、类型和区间感知的数组约束求解、编译增强型符号执行等创新方法显著提升了符号执行的效率和可扩展性。在实现层面，模块化架构设计、交互式调试平台、硬件加速技术等进步降低了符号执行的使用门槛，扩展了其应用范围。在应用层面，符号执行在自动化测试用例生成、智能合约安全审计、科学计算验证等领域展现出巨大价值。
然而，符号执行仍面临诸多挑战。路径爆炸问题、约束求解复杂性、环境交互建模困难等限制了符号执行在大规模复杂系统中的应用。同时，符号执行工具的易用性、与开发流程的集成度、结果的可解释性等方面仍有改进空间。
未来研究方向
1. 智能化的符号执行策略优化
未来的符号执行系统需要更加智能化的策略优化机制。结合机器学习技术，系统能够根据程序特征和历史数据自适应调整符号执行策略，平衡探索深度和广度。Chen等人的自适应求解策略合成已在此方向迈出重要一步，但更深入的集成学习和在线优化仍是未来研究重点。此类方法有望解决路径选择、约束求解优先级等关键决策问题，显著提升符号执行效率。
2. 领域特定的符号执行框架开发
针对特定领域的符号执行框架将提高分析精度和效率。Lin等人的SolSEE为Solidity智能合约提供了源级符号执行引擎，类似地，针对科学计算、嵌入式系统、并发程序等领域的专用框架亟待开发。这些框架能够利用领域知识优化符号执行过程，处理领域特定的数据结构和运算规则，提供更精准的分析结果。Cisneros-Garibay的Pyrometheus在燃烧热化学领域的实践为此提供了范例。开发此类专用工具时，对编程语言及生态系统进行系统性评估和选择至关重要，以确保工具的长期可维护性和社区支持[16]。
3. 符号执行与软件工程流程的深度融合
符号执行技术需要更好地融入软件开发生命周期。未来的研究方向包括开发与持续集成/持续部署（CI/CD）管道集成的符号执行工具，实现自动化的代码质量检查和安全审计；构建交互式符号执行环境，支持开发者在编码过程中实时验证程序性质；以及开发面向非专家用户的符号执行服务，降低技术使用门槛。Hentschel的SED平台为交互式符号执行提供了基础，但更广泛的工程化应用仍需探索。
4. 跨学科融合与新兴技术结合
符号执行与新兴计算技术的结合将开拓新的应用领域。与量子计算结合，发展量子程序的符号执行方法；与区块链技术结合，提供更强大的智能合约分析能力；与人工智能结合，实现基于符号执行的可解释AI验证。同时，符号执行技术也需要吸收形式化方法、程序分析、软件测试等领域的成果，形成更加完善的理论体系和技术生态。Lu等人的AI科学家框架展示了自动化科学研究流程的潜力，类似思想可应用于软件开发过程。此外，符号执行在科学计算中的应用可进一步与先进的科学数据可视化技术[5]结合，使复杂程序状态和约束求解结果的分析更加直观高效。
符号执行作为连接程序理论与实践验证的桥梁，在软件质量保障和系统可靠性方面发挥着不可替代的作用。随着计算技术的不断进步和应用需求的日益增长，符号执行必将在更多领域展现其价值，为构建可信赖的软件系统提供坚实的技术基础。未来的研究需要在算法效率、工程实用性和领域适应性等方面持续创新，推动符号执行技术向更智能、更高效、更易用的方向发展。
参考文献
[1] Chris Lu, Cong Lu, R. Lange, 等. The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. 2024.
[2] Aidan P. Thompson, Hasan Metin Aktulga, Richard Berger, 等. LAMMPS - a flexible simulation tool for particle-based materials modeling at the atomic, meso, and continuum scales. 2021. DOI: https://doi.org/10.1016/j.cpc.2021.108171
[3] Salvatore Cuomo, Vincenzo Schiano Di Cola, Fabio Giampaolo, 等. Scientific Machine Learning Through Physics–Informed Neural Networks: Where we are and What’s Next. 2022. DOI: https://doi.org/10.1007/s10915-022-01939-z
[4] Yi Luan, Luheng He, Mari Ostendorf, 等. Multi-Task Identification of Entities, Relations, and Coreference for Scientific Knowledge Graph Construction. 2018. DOI: https://doi.org/10.18653/v1/d18-1360
[5] Zhiyu Yang, Zihan Zhou, Shuo Wang, 等. MatPlotAgent: Method and Evaluation for LLM-Based Agentic Scientific Data Visualization. arXiv preprint arXiv:2402.11453
[6] Sebastian Poeplau, Aurélien Francillon. SymQEMU: Compilation-based symbolic execution for binaries[C]//Proceedings 2021 Network and Distributed System Security Symposium. 2021. DOI: 10.14722/NDSS.2021.24118
[7] Srijoni Majumdar, Ayush Bansal, P. Das, 等. Automated evaluation of comments to aid software maintenance. 2022. DOI: 10.1002/smr.2463
[8] Ting Su, G. Pu, Weikai Miao, 等. Automated coverage-driven testing: combining symbolic execution and model checking[J]. Science China Information Sciences, 2016. DOI: 10.1007/s11432-016-5589-6
[9] Esteban Cisneros-Garibay, H. L. Berre, Spencer H. Bryngelson, 等. Pyrometheus: Symbolic abstractions for XPU and automatically differentiated computation of combustion kinetics and thermodynamics[J]. Comput. Phys. Commun., 2025. DOI: 10.1016/j.cpc.2025.109987
[10] Andrei Arusoaie, D. Lucanu. Proof-carrying parameters in certified symbolic execution[J]. Log. J. IGPL, 2023. DOI: 10.1093/jigpal/jzad008
[11] D.M. Spiridonov, D. Obukhovich. Analytical and computer software mathematical models of the noise of the output signal of a fiber-optic gyroscope, analysis and verification[J]. Journal of Radio Electronics, 2024. DOI: 10.30898/1684-1719.2024.3.7
[12] Zhenbang Chen, Guofeng Zhang, Zehua Chen, 等. Adaptive solving strategy synthesis for symbolic execution[J]. Journal of Software: Evolution and Process, 2023. DOI: 10.1002/smr.2568
[13] Erik Voogd, Åsmund Aqissiaq Arild Kløvstad, E. Johnsen, 等. Compositional symbolic execution semantics[J]. Theor. Comput. Sci., 2025. DOI: 10.1016/j.tcs.2025.115263
[14] Renhua Wu, Yi Qiu. SmartAudiTor: a hybrid smart contract vulnerability auditing framework based on LLM-guided and symbolic execution verification. 2026. DOI: 10.1117/12.3103304
[15] Shun-Feng Su, Meng Chang. Adaptive neural acceleration unit based on heterogeneous multicore hardware architecture FPGA and software-defined hardware[J]. Journal of the Chinese Institute of Engineers, 2024. DOI: 10.1080/02533839.2024.2308249
[16] Siamak Farshidi. A decision model for programming language ecosystem selection: Seven industry case studies. 2021. DOI: 10.1016/J.INFSOF.2021.106640
[17] Zhenbang Chen, Zehua Chen, Ziqi Shuai, 等. Synthesize solving strategy for symbolic execution[C]//Proceedings of the 30th ACM SIGSOFT International Symposium on Software Testing and Analysis. 2021. DOI: 10.1145/3460319.3464815
[18] Ziqi Shuai, Zhenbang Chen, Yufeng Zhang, 等. Type and interval aware array constraint solving for symbolic execution[C]//Proceedings of the 30th ACM SIGSOFT International Symposium on Software Testing and Analysis. 2021. DOI: 10.1145/3460319.3464826
[19] Shang-Wei Lin, Palina Tolmach, Ye Liu, 等. SolSEE: a source-level symbolic execution engine for solidity[C]//Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering. 2022. DOI: 10.1145/3540250.3558923
[20] Sicheng Luo, Hui Xu, Yanxiang Bi, 等. Boosting symbolic execution via constraint solving time prediction (experience paper)[C]//Proceedings of the 30th ACM SIGSOFT International Symposium on Software Testing and Analysis. 2021. DOI: 10.1145/3460319.3464813
[21] Dorel Lucanu, Vlad Rusu, Andrei Arusoaie. A generic framework for symbolic execution: A coinductive approach. 2017. DOI: 10.1016/j.jsc.2016.07.012
[22] David Trabish, N. Rinetzky. Relocatable addressing model for symbolic execution[C]//Proceedings of the 29th ACM SIGSOFT International Symposium on Software Testing and Analysis. 2020. DOI: 10.1145/3395363.3397363
[23] Martin Hentschel, Richard Bubel, Reiner Hähnle. The Symbolic Execution Debugger (SED): a platform for interactive symbolic execution, debugging, verification and more. 2019. DOI: 10.1007/s10009-018-0490-9
[24] Jens Knoop, Laura Kovács, Jakob Zwirchmayr. Replacing conjectures by positive knowledge: Inferring proven precise worst-case execution time bounds using symbolic execution. 2017. DOI: 10.1016/j.jsc.2016.07.023
[25] 张伟杰 Zhang Weijie, 宋开山 Song Kaishan. Design of random laser and feature verification of FDTD software with the infrared wavelengths. 2016. DOI: 10.3788/irla20164511.1105006
[26] Haijiang Zhou. ON TEST CASE GENERATION BASED ON SYMBOLIC EXECUTION AND HYBRID CONSTRAINT SOLVING. 2016. DOI: 10.3969/j.issn.1000-386x.2016.06.006
