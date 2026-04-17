基于双向长短期记忆网络和卷积神经网络的DNA 6mA甲基化位点预测

文献统计：文献总数：14篇 | 近5年文献占比：71.4% | 英文文献占比：100.0% | 总被引量：82308次
引言
DNA N6-甲基腺嘌呤（6mA）作为一种进化上保守的表观遗传修饰，在真核生物中发挥着关键的调控作用。它通过影响染色质结构、DNA-蛋白质相互作用以及转录过程，广泛参与基因表达调控、胚胎发育、细胞分化以及环境应激响应等基本生物学过程[1]。近年来，研究进一步表明，6mA修饰的异常与多种人类疾病，包括癌症、神经退行性疾病和代谢紊乱的发生发展密切相关，凸显了其在生物医学研究中的重要价值[2]。因此，精确绘制和解析基因组中的6mA位点图谱，对于深入理解生命活动的表观遗传调控机制及疾病机理至关重要。
传统上，6mA位点的鉴定主要依赖于基于测序的实验技术，如6mA-IP-seq和单分子实时测序。然而，这些实验方法通常成本高昂、耗时费力，且难以实现高通量、高分辨率的全基因组筛查[3]。为了克服这些局限性，计算预测方法，特别是基于深度学习的算法，已成为一种高效且经济的补充策略。这些方法能够从已知的DNA序列和修饰数据中学习识别6mA位点的特征模式，从而对未知序列进行快速、准确的位点预测。
在众多深度学习架构中，结合双向长短期记忆网络（Bi-directional LSTM）与卷积神经网络（CNN）的混合模型，在生物信息学序列分析任务中展现出独特优势。具体到6mA位点预测这一特定场景，其优势尤为明显：DNA序列具有方向性的生物学意义（如5‘-3’方向），双向LSTM能够从前向和后向两个维度捕获序列中长距离的依赖关系和上下文信息，这对于理解可能跨越多个核苷酸的调控信号至关重要。与此同时，CNN擅长通过卷积核自动提取序列中局部、高维的基序（motif）和空间模式，这些模式往往是酶结合或修饰的特异性序列特征。将两者结合，可以协同建模DNA序列的全局上下文语义与局部功能基序，为6mA位点的精准预测提供了强大的框架[4]。
目前，针对6mA位点预测的计算研究已取得一系列进展，但专门系统探讨和综述双向LSTM与CNN混合模型在此领域应用的工作仍显不足。本综述旨在系统回顾基于双向LSTM-CNN混合模型的DNA 6mA位点预测方法。我们将重点分析该特定场景下的核心挑战与解决方案，包括：如何针对DNA字符序列（A, T, C, G）进行有效的特征表示与编码；如何处理因基因组中修饰位点远少于非修饰位点而导致的严重类别不平衡问题；以及如何有效整合已知的生物学特征（如序列保守性、染色质可及性等）以提升模型的生物学可解释性和预测性能。通过梳理现有方法、比较其优劣并展望未来方向，以期为该领域的进一步发展提供参考。
**DNA 6mA甲基化的生物学背景与预测挑战**
DNA N6-甲基腺嘌呤（6mA）是一种在真核生物中重新受到关注的表观遗传修饰。与在哺乳动物中研究较为透彻的5-甲基胞嘧啶（5mC）不同，6mA在真核基因组中的丰度相对较低，但其生物学功能日益凸显。文献[1]和[2]系统综述了6mA在人类及其他哺乳动物基因组中的分布，指出其富集于基因启动子、增强子等调控区域，并与转录激活、转座子沉默等过程相关。例如，在环境响应方面，文献[5]的案例研究表明，6mA修饰水平会响应环境胁迫而发生动态变化，提示其可能作为环境-基因互作的表观遗传桥梁。此外，文献[6]揭示了6mA在线粒体DNA中的存在及其潜在功能，拓展了我们对这一修饰在亚细胞器水平作用的认识。这些研究共同表明，6mA是一种具有重要调控功能的表观遗传标记，其异常与疾病发生发展密切相关。
本场景的特殊性在于，预测6mA位点并非一个通用的序列分类问题，而是针对一种特定、稀疏的DNA化学修饰的模式识别。 与5mC相比，6mA在基因组中的位点更为稀疏，其侧翼序列模式（motif）可能具有物种特异性，这直接增加了从DNA一级序列中识别其信号模式的难度。此外，实验检测6mA的技术（如文献[3]提到的酶学甲基测序）成本高昂且通量有限，导致高质量、大规模的标注数据稀缺，这构成了预测模型开发的首要瓶颈。这种数据稀缺性在生物信息学预测任务中普遍存在，例如在蛋白质结构预测领域，AlphaFold2[7]的成功也高度依赖于对有限已知结构数据的高效学习和对进化信息的深度挖掘。同样，在预测生物分子相互作用时，模型也需要从稀疏的相互作用数据中学习复杂的模式[8]。
预测6mA位点面临多重生物信息学挑战，首要挑战是数据表示与类别不平衡。DNA序列通常被转化为数值向量，如one-hot编码，但如何有效编码核苷酸的化学属性或高阶序列特征是关键。文献[9]在5mC相关研究中提及的序列上下文重要性，同样适用于6mA，因为甲基转移酶的特异性依赖于核心腺嘌呤周围的特定核苷酸排列。更严峻的挑战是类别不平衡，即甲基化位点（正样本）的数量远少于非甲基化位点（负样本）。不同研究采用了不同的策略来处理此问题，如下表所示：
| 处理策略 | 核心思想 | 潜在优势 | 潜在局限 | 相关文献/场景 |
| :--- | :--- | :--- | :--- | :--- |
| 下采样 | 随机减少多数类（非甲基化）样本数量，使类别平衡。 | 简单直接，计算成本低。 | 丢弃大量潜在信息，可能影响模型学习全局序列背景。 | 常见于早期或数据量相对充足的6mA预测研究。 |
| 上采样/数据增强 | 通过人工合成或复制少数类（甲基化）样本增加其数量。 | 保留所有原始样本信息。 | 简单的复制可能导致过拟合；合成样本的真实性难以保证。 | 在6mA预测中，需谨慎设计以避免引入虚假序列模式。 |
| 集成学习/代价敏感学习 | 在算法层面赋予少数类更高的错分惩罚权重。 | 无需修改原始数据分布，更充分利用数据。 | 权重设置需要调优，可能增加模型训练复杂度。 | 更适合于处理极端不平衡的6mA数据集。 |
本场景的另一个特异性挑战在于序列长度变异和特征整合。 用于预测的DNA片段长度需要既能捕获足够的上下文信息，又不会引入过多噪音。同时，除了原始序列，是否及如何整合其他生物特征（如染色质可及性、组蛋白修饰等表观遗传标记）以提升预测性能，是一个开放性问题。目前，大多数研究仍聚焦于从序列本身挖掘信息，这凸显了开发强大序列特征提取模型的必要性。综上所述，6mA预测的独特性要求方法学必须针对性解决其数据稀疏性、模式隐蔽性及生物学背景的复杂性。这种对模型鲁棒性和泛化能力的高要求，与气候模型[10]、流行病学模型[48, 49]以及临床预测模型[4, 45]等领域所面临的挑战有共通之处，即都需要在复杂、高维且可能存在偏差的数据中建立可靠的预测关系。
**基于双向LSTM和CNN的深度学习模型在6mA预测中的应用**
深度学习，特别是循环神经网络（RNN）和卷积神经网络（CNN），已广泛应用于生物序列分析。文献[11]系统阐述了长短期记忆网络（LSTM）处理序列依赖关系的原理，为将其应用于DNA序列建模奠定了理论基础。在6mA预测这一具体任务中，研究者们开始探索结合双向LSTM（BiLSTM）和CNN的混合架构，以同时捕获序列的长期依赖关系和局部保守模式。这种混合架构的设计思想与分子动力学模拟软件LAMMPS[12]中整合多种计算方法的理念类似，旨在通过组合不同优势的模块来更全面地描述复杂系统。
本场景的核心技术路径是构建BiLSTM-CNN混合模型，其设计理念直接针对DNA序列的双重特性：局部序列模式（如转录因子结合位点）和长程上下文依赖（如染色质结构域的影响）。 CNN层充当局部特征探测器，从滑动窗口中的短核苷酸片段中提取诸如k-mer频率、基序等局部模式；而BiLSTM层则能从前向和后向两个方向学习整个输入序列的上下文信息，理解更广泛的序列语法。文献[13]提出的模型是这一思路的典型代表，其架构通常为先CNN后BiLSTM，即CNN提取局部特征图，再由BiLSTM学习这些特征在序列上的时序关系。文献[14]（6mA-...
参考文献
[1]John Jumper,Richard Evans,Alexander Pritzel,等.Highly accurate protein structure prediction with AlphaFold[J].2021.DOI:https://doi.org/10.1038/s41586-021-03819-2.
[2]Josh Abramson,Jonas Adler,Jack Dunger,等.Accurate structure prediction of biomolecular interactions with AlphaFold 3[J].2024.DOI:https://doi.org/10.1038/s41586-024-07487-w.
[3]伟 高.Prediction of DNA 6mA Methylation Sites Based on Bidirectional Long Short-Term Memory Network and Convolutional Neural Network[J].2024.DOI:10.12677/hjcb.2024.143003.
[4]Aidan P. Thompson,Hasan Metin Aktulga,Richard Berger,等.LAMMPS - a flexible simulation tool for particle-based materials modeling at the atomic, meso, and continuum scales[J].2021.DOI:https://doi.org/10.1016/j.cpc.2021.108171.
[5]Chuan-Le Xiao.N6-Methyladenine DNA Modification in the Human Genome.[J].2018.DOI:10.1016/j.molcel.2018.06.015.
[6]Jianzhong Cao.Supplementary Table 2 from DNA Methylation-Mediated Repression of Mir-886-3p Predicts Poor Outcome of Human Small Cell Lung Cancer[J].2023.DOI:10.1158/0008-5472.22397201.v1.
[7]Veronika Eyring,Sandrine Bony,Gerald A. Meehl,等.Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization[J].2016.DOI:https://doi.org/10.5194/gmd-9-1937-2016.
[8]Romualdas Vaisvila.Enzymatic Methyl Sequencing Detects DNA Methylation at Single-Base Resolution from Picograms of DNA[J].2021.DOI:10.1101/gr.266551.120.
[9]Chao Shen.DNA N6-methyldeoxyadenosine in Mammals and Human Disease.[J].2022.DOI:10.1016/j.tig.2021.12.003.
[10]Yalan Sheng.Case Study of the Response of N6-Methyladenine DNA Modification to Environmental Stressors in the Unicellular Eukaryote Tetrahymena Thermophila.[J].2021.DOI:10.1128/msphere.01208-20.
[11]Sho Tsukiyama.BERT6mA: Prediction of DNA N6-methyladenine Site Using Deep Learning-Based Approaches.[J].2022.DOI:10.1093/bib/bbac053.
[12]Ziyang Hao.N6-Deoxyadenosine Methylation in Mammalian Mitochondrial DNA.[J].2020.DOI:10.1016/j.molcel.2020.02.018.
[13]Alex Sherstinsky.Fundamentals of Recurrent Neural Network (RNN) and Long Short-Term Memory (LSTM) Network[J].2020.DOI:10.1016/j.physd.2019.132306.
[14]Qianfei Huang.6Ma-Pred: Identifying DNA N6-methyladenine Sites Based on Deep Learning[J].2021.DOI:10.7717/peerj.10813.

